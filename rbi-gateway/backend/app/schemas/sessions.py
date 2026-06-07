from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    target_url: str
    profile_id: str | None = None
    mode: Literal["persistent", "ephemeral"] = "persistent"
    ttl_minutes: int = Field(default=60, ge=1, le=1440)


class SessionCreateResponse(BaseModel):
    session_id: str
    viewer_url: str
    expires_at: datetime
    status: Literal["running", "stopped", "expired"]


class SessionNavigateRequest(BaseModel):
    target_url: str


class SessionStatusResponse(BaseModel):
    session_id: str
    status: Literal["running", "stopped", "expired"]
    expires_at: datetime | None = None
