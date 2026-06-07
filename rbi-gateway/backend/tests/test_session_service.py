import pytest

from app.schemas.sessions import SessionCreateRequest
from app.services.session_service import InMemorySessionStore, SessionService


class FakeManagerClient:
    def __init__(self) -> None:
        self.created_profiles: list[dict] = []
        self.launched_profiles: list[str] = []
        self.stopped_profiles: list[str] = []

    async def create_profile(self, payload: dict) -> dict:
        self.created_profiles.append(payload)
        return {"id": "manager-profile-1"}

    async def launch_profile(self, manager_profile_id: str) -> dict:
        self.launched_profiles.append(manager_profile_id)
        return {
            "profile_id": manager_profile_id,
            "status": "running",
            "cdp_url": f"/api/profiles/{manager_profile_id}/cdp",
        }

    async def stop_profile(self, manager_profile_id: str) -> None:
        self.stopped_profiles.append(manager_profile_id)


class FakeCdpService:
    def __init__(self) -> None:
        self.opened: list[tuple[str, str]] = []
        self.reloaded: list[str] = []

    async def open_url(self, session, target_url: str) -> None:
        self.opened.append((session.id, target_url))

    async def reload(self, session) -> None:
        self.reloaded.append(session.id)


@pytest.mark.asyncio
async def test_create_session_launches_manager_profile_and_opens_url() -> None:
    store = InMemorySessionStore()
    manager = FakeManagerClient()
    cdp = FakeCdpService()
    service = SessionService(store=store, manager_client=manager, cdp_service=cdp)

    response = await service.create_session(
        user_id="user-1",
        request=SessionCreateRequest(target_url="https://example.com", ttl_minutes=30),
    )

    assert response.status == "running"
    assert response.viewer_url.startswith("/session/")
    assert "example.com" not in response.viewer_url
    assert manager.created_profiles[0]["name"].startswith("RBI Profile")
    assert manager.launched_profiles == ["manager-profile-1"]
    assert cdp.opened == [(response.session_id, "https://example.com")]

    stored = store.sessions[response.session_id]
    assert stored.viewer_token_hash
    assert not hasattr(stored, "viewer_token")
    assert stored.target_url_encrypted != "https://example.com"


@pytest.mark.asyncio
async def test_navigate_validates_and_opens_url_without_returning_target_url() -> None:
    store = InMemorySessionStore()
    manager = FakeManagerClient()
    cdp = FakeCdpService()
    service = SessionService(store=store, manager_client=manager, cdp_service=cdp)
    created = await service.create_session(
        user_id="user-1",
        request=SessionCreateRequest(target_url="https://example.com", ttl_minutes=30),
    )

    response = await service.navigate(
        user_id="user-1",
        session_id=created.session_id,
        target_url="https://example.org/new?secret=value",
    )

    assert response.session_id == created.session_id
    assert response.status == "running"
    assert "example.org" not in response.model_dump_json()
    assert cdp.opened[-1] == (created.session_id, "https://example.org/new?secret=value")


@pytest.mark.asyncio
async def test_stop_session_invalidates_viewer_token_and_stops_manager_profile() -> None:
    store = InMemorySessionStore()
    manager = FakeManagerClient()
    service = SessionService(store=store, manager_client=manager, cdp_service=FakeCdpService())
    created = await service.create_session(
        user_id="user-1",
        request=SessionCreateRequest(target_url="https://example.com", ttl_minutes=30),
    )

    await service.stop_session(user_id="user-1", session_id=created.session_id)

    stored = store.sessions[created.session_id]
    assert stored.status == "stopped"
    assert stored.viewer_token_hash is None
    assert manager.stopped_profiles == ["manager-profile-1"]
