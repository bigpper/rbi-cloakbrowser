from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas.sessions import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionNavigateRequest,
    SessionStatusResponse,
)
from app.services.url_policy_service import UrlPolicyError

router = APIRouter(prefix="/api/rbi/sessions", tags=["sessions"])


def _user_id(request: Request) -> str:
    # MVP auth shim. Replace with real auth before production exposure.
    return request.headers.get("x-user-id", "demo-user")


@router.post("", response_model=SessionCreateResponse)
async def create_session(request_body: SessionCreateRequest, request: Request):
    try:
        return await request.app.state.session_service.create_session(_user_id(request), request_body)
    except UrlPolicyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{session_id}/navigate", response_model=SessionStatusResponse)
async def navigate_session(session_id: str, request_body: SessionNavigateRequest, request: Request):
    try:
        return await request.app.state.session_service.navigate(
            user_id=_user_id(request),
            session_id=session_id,
            target_url=request_body.target_url,
        )
    except UrlPolicyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{session_id}/stop", response_model=SessionStatusResponse)
async def stop_session(session_id: str, request: Request):
    try:
        return await request.app.state.session_service.stop_session(_user_id(request), session_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{session_id}/reload", response_model=SessionStatusResponse)
async def reload_session(session_id: str, request: Request):
    try:
        return await request.app.state.session_service.reload(_user_id(request), session_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{session_id}/back", response_model=SessionStatusResponse)
async def back_session(session_id: str, request: Request):
    try:
        return await request.app.state.session_service.go_back(_user_id(request), session_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{session_id}/forward", response_model=SessionStatusResponse)
async def forward_session(session_id: str, request: Request):
    try:
        return await request.app.state.session_service.go_forward(_user_id(request), session_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
