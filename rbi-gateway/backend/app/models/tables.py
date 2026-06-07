from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RbiProfile(Base):
    __tablename__ = "rbi_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    manager_profile_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    proxy_encrypted: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str | None] = mapped_column(String(128))
    locale: Mapped[str | None] = mapped_column(String(32))
    screen_width: Mapped[int] = mapped_column(Integer, default=1280)
    screen_height: Mapped[int] = mapped_column(Integer, default=720)
    persistent: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RbiSession(Base):
    __tablename__ = "rbi_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    profile_id: Mapped[str] = mapped_column(String(64), ForeignKey("rbi_profiles.id"), nullable=False, index=True)
    manager_profile_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target_url_encrypted: Mapped[str | None] = mapped_column(Text)
    viewer_token_hash: Mapped[str | None] = mapped_column(String(128), unique=True)
    audio_token_hash: Mapped[str | None] = mapped_column(String(128), unique=True)
    display_profile: Mapped[str] = mapped_column(String(32), nullable=False, default="high")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    cdp_endpoint_internal: Mapped[str | None] = mapped_column(Text)
    viewer_endpoint_internal: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    session_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("rbi_sessions.id"))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    domain_hash: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
