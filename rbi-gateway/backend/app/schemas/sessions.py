from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DisplayProfile = Literal["high", "medium", "low"]


class SessionCreateRequest(BaseModel):
    target_url: str
    profile_id: str | None = None
    mode: Literal["persistent", "ephemeral"] = "persistent"
    ttl_minutes: int = Field(default=60, ge=1, le=1440)
    display_profile: DisplayProfile = "high"


class SessionCreateResponse(BaseModel):
    session_id: str
    viewer_url: str
    expires_at: datetime
    status: Literal["running", "stopped", "expired"]


class SessionNavigateRequest(BaseModel):
    target_url: str


class SessionTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)


class SessionDisplayProfileRequest(BaseModel):
    display_profile: DisplayProfile


class SessionStatusResponse(BaseModel):
    session_id: str
    status: Literal["running", "stopped", "expired"]
    expires_at: datetime | None = None
