from __future__ import annotations

from pydantic import BaseModel, Field


class ProxyConfig(BaseModel):
    type: str = Field(pattern="^(http|socks5)$")
    host: str
    port: int
    username: str | None = None
    password: str | None = None


class ScreenConfig(BaseModel):
    width: int = 1280
    height: int = 720


class ProfileCreateRequest(BaseModel):
    name: str
    proxy: ProxyConfig | None = None
    timezone: str | None = None
    locale: str | None = "en-US"
    screen: ScreenConfig = Field(default_factory=ScreenConfig)
    persistent: bool = True


class ProfileResponse(BaseModel):
    id: str
    name: str
    manager_profile_id: str
    timezone: str | None = None
    locale: str | None = None
    screen: ScreenConfig
    persistent: bool
    status: str = "active"
