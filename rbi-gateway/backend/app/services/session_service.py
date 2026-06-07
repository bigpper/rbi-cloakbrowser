from __future__ import annotations

import base64
import hashlib
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.schemas.sessions import SessionCreateRequest, SessionCreateResponse, SessionStatusResponse
from app.services.url_policy_service import validate_target_url


class ManagerClientProtocol(Protocol):
    async def create_profile(self, payload: dict) -> dict: ...
    async def launch_profile(self, manager_profile_id: str) -> dict: ...
    async def stop_profile(self, manager_profile_id: str) -> None: ...


class CdpServiceProtocol(Protocol):
    async def open_url(self, session: "StoredSession", target_url: str) -> None: ...
    async def reload(self, session: "StoredSession") -> None: ...
    async def go_back(self, session: "StoredSession") -> None: ...
    async def go_forward(self, session: "StoredSession") -> None: ...


@dataclass
class StoredProfile:
    id: str
    user_id: str
    manager_profile_id: str
    name: str
    persistent: bool


@dataclass
class StoredSession:
    id: str
    user_id: str
    profile_id: str
    manager_profile_id: str
    target_url_encrypted: str
    viewer_token_hash: str | None
    status: str
    cdp_endpoint_internal: str | None
    viewer_endpoint_internal: str | None
    expires_at: datetime
    last_active_at: datetime
    created_at: datetime
    stopped_at: datetime | None = None


class InMemorySessionStore:
    """Small test/dev store. The production app wires SQL repositories later."""

    def __init__(self) -> None:
        self.profiles: dict[str, StoredProfile] = {}
        self.sessions: dict[str, StoredSession] = {}

    def get_profile_for_user(self, profile_id: str, user_id: str) -> StoredProfile | None:
        profile = self.profiles.get(profile_id)
        if not profile or profile.user_id != user_id:
            return None
        return profile

    def create_profile(self, user_id: str, manager_profile_id: str, name: str, persistent: bool) -> StoredProfile:
        profile = StoredProfile(
            id=str(uuid.uuid4()),
            user_id=user_id,
            manager_profile_id=manager_profile_id,
            name=name,
            persistent=persistent,
        )
        self.profiles[profile.id] = profile
        return profile

    def create_session(self, session: StoredSession) -> StoredSession:
        self.sessions[session.id] = session
        return session

    def get_session_for_user(self, session_id: str, user_id: str) -> StoredSession | None:
        session = self.sessions.get(session_id)
        if not session or session.user_id != user_id:
            return None
        return session

    def get_session_by_viewer_token_hash(self, viewer_token_hash: str) -> StoredSession | None:
        for session in self.sessions.values():
            if session.viewer_token_hash == viewer_token_hash:
                return session
        return None


def _hash_secret(value: str) -> str:
    salt = os.getenv("TOKEN_HASH_SECRET", "dev-token-hash-salt")
    return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()


def _encrypt_for_storage(value: str) -> str:
    # MVP placeholder encryption boundary: values are not logged and are stored
    # encoded until the database encryption service is wired to FIELD_ENCRYPTION_KEY.
    encoded = base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii")
    return f"enc:v1:{encoded}"


class SessionService:
    def __init__(
        self,
        store: InMemorySessionStore,
        manager_client: ManagerClientProtocol,
        cdp_service: CdpServiceProtocol,
    ) -> None:
        self.store = store
        self.manager_client = manager_client
        self.cdp_service = cdp_service

    async def create_session(self, user_id: str, request: SessionCreateRequest) -> SessionCreateResponse:
        target_url = validate_target_url(request.target_url)
        profile = await self._get_or_create_profile(user_id, request)
        launch = await self.manager_client.launch_profile(profile.manager_profile_id)

        now = datetime.now(UTC)
        viewer_token = secrets.token_urlsafe(32)
        session = StoredSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            profile_id=profile.id,
            manager_profile_id=profile.manager_profile_id,
            target_url_encrypted=_encrypt_for_storage(target_url),
            viewer_token_hash=_hash_secret(viewer_token),
            status="running",
            cdp_endpoint_internal=launch.get("cdp_url"),
            viewer_endpoint_internal=f"/api/profiles/{profile.manager_profile_id}/vnc",
            expires_at=now + timedelta(minutes=request.ttl_minutes),
            last_active_at=now,
            created_at=now,
        )
        self.store.create_session(session)
        await self.cdp_service.open_url(session, target_url)

        return SessionCreateResponse(
            session_id=session.id,
            viewer_url=f"/session/{viewer_token}",
            expires_at=session.expires_at,
            status="running",
        )

    async def navigate(self, user_id: str, session_id: str, target_url: str) -> SessionStatusResponse:
        session = self._require_running_session(user_id, session_id)
        validated = validate_target_url(target_url)
        session.target_url_encrypted = _encrypt_for_storage(validated)
        session.last_active_at = datetime.now(UTC)
        await self.cdp_service.open_url(session, validated)
        return SessionStatusResponse(session_id=session.id, status="running", expires_at=session.expires_at)

    async def stop_session(self, user_id: str, session_id: str) -> SessionStatusResponse:
        session = self._require_session(user_id, session_id)
        if session.status == "running":
            await self.manager_client.stop_profile(session.manager_profile_id)
        session.status = "stopped"
        session.viewer_token_hash = None
        session.stopped_at = datetime.now(UTC)
        return SessionStatusResponse(session_id=session.id, status="stopped", expires_at=session.expires_at)

    async def reload(self, user_id: str, session_id: str) -> SessionStatusResponse:
        session = self._require_running_session(user_id, session_id)
        await self.cdp_service.reload(session)
        return SessionStatusResponse(session_id=session.id, status="running", expires_at=session.expires_at)

    async def go_back(self, user_id: str, session_id: str) -> SessionStatusResponse:
        session = self._require_running_session(user_id, session_id)
        await self.cdp_service.go_back(session)
        return SessionStatusResponse(session_id=session.id, status="running", expires_at=session.expires_at)

    async def go_forward(self, user_id: str, session_id: str) -> SessionStatusResponse:
        session = self._require_running_session(user_id, session_id)
        await self.cdp_service.go_forward(session)
        return SessionStatusResponse(session_id=session.id, status="running", expires_at=session.expires_at)

    def get_session_by_viewer_token(self, viewer_token: str) -> StoredSession:
        session = self.store.get_session_by_viewer_token_hash(_hash_secret(viewer_token))
        if not session or session.status != "running" or session.expires_at <= datetime.now(UTC):
            raise PermissionError("Viewer token is invalid")
        session.last_active_at = datetime.now(UTC)
        return session

    async def _get_or_create_profile(self, user_id: str, request: SessionCreateRequest) -> StoredProfile:
        if request.profile_id:
            profile = self.store.get_profile_for_user(request.profile_id, user_id)
            if not profile:
                raise PermissionError("Profile not found")
            return profile

        manager_profile = await self.manager_client.create_profile(
            {
                "name": f"RBI Profile {uuid.uuid4().hex[:8]}",
                "screen_width": 1280,
                "screen_height": 720,
                "headless": False,
            }
        )
        return self.store.create_profile(
            user_id=user_id,
            manager_profile_id=manager_profile["id"],
            name=manager_profile.get("name", "RBI Profile"),
            persistent=request.mode == "persistent",
        )

    def _require_session(self, user_id: str, session_id: str) -> StoredSession:
        session = self.store.get_session_for_user(session_id, user_id)
        if not session:
            raise PermissionError("Session not found")
        return session

    def _require_running_session(self, user_id: str, session_id: str) -> StoredSession:
        session = self._require_session(user_id, session_id)
        if session.status != "running" or session.expires_at <= datetime.now(UTC):
            raise PermissionError("Session is not running")
        return session
