from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/rbi/auth", tags=["auth"])


@router.get("/me")
async def me() -> dict[str, str]:
    # MVP placeholder. Production should replace this with real authentication.
    return {"id": "demo-user", "email": "demo@example.local", "status": "active"}
