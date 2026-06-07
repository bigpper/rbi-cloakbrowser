from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas.profiles import ProfileCreateRequest, ProfileResponse, ScreenConfig

router = APIRouter(prefix="/api/rbi/profiles", tags=["profiles"])


def _user_id(request: Request) -> str:
    return request.headers.get("x-user-id", "demo-user")


def _profile_response(profile) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        name=profile.name,
        manager_profile_id=profile.manager_profile_id,
        screen=ScreenConfig(width=1280, height=720),
        persistent=profile.persistent,
        status="active",
    )


@router.get("", response_model=list[ProfileResponse])
async def list_profiles(request: Request):
    user_id = _user_id(request)
    profiles = [p for p in request.app.state.store.profiles.values() if p.user_id == user_id]
    return [_profile_response(profile) for profile in profiles]


@router.post("", response_model=ProfileResponse, status_code=201)
async def create_profile(body: ProfileCreateRequest, request: Request):
    manager_payload = {
        "name": body.name,
        "timezone": body.timezone,
        "locale": body.locale,
        "screen_width": body.screen.width,
        "screen_height": body.screen.height,
        "headless": False,
    }
    if body.proxy:
        auth = ""
        if body.proxy.username and body.proxy.password:
            auth = f"{body.proxy.username}:{body.proxy.password}@"
        manager_payload["proxy"] = f"{body.proxy.type}://{auth}{body.proxy.host}:{body.proxy.port}"

    manager_profile = await request.app.state.manager_client.create_profile(manager_payload)
    profile = request.app.state.store.create_profile(
        user_id=_user_id(request),
        manager_profile_id=manager_profile["id"],
        name=body.name,
        persistent=body.persistent,
    )
    return _profile_response(profile)


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: str, request: Request):
    profile = request.app.state.store.get_profile_for_user(profile_id, _user_id(request))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _profile_response(profile)


@router.patch("/{profile_id}", response_model=ProfileResponse)
async def update_profile(profile_id: str, body: ProfileCreateRequest, request: Request):
    profile = request.app.state.store.get_profile_for_user(profile_id, _user_id(request))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    await request.app.state.manager_client.update_profile(
        profile.manager_profile_id,
        {
            "name": body.name,
            "timezone": body.timezone,
            "locale": body.locale,
            "screen_width": body.screen.width,
            "screen_height": body.screen.height,
        },
    )
    profile.name = body.name
    profile.persistent = body.persistent
    return _profile_response(profile)


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str, request: Request):
    profile = request.app.state.store.get_profile_for_user(profile_id, _user_id(request))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    request.app.state.store.profiles.pop(profile_id, None)
    return {"ok": True}
