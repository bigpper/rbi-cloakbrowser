"""initial rbi gateway schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "rbi_profiles",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("manager_profile_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("proxy_encrypted", sa.Text()),
        sa.Column("timezone", sa.String(length=128)),
        sa.Column("locale", sa.String(length=32)),
        sa.Column("screen_width", sa.Integer(), nullable=False, server_default="1280"),
        sa.Column("screen_height", sa.Integer(), nullable=False, server_default="720"),
        sa.Column("persistent", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_rbi_profiles_user_id", "rbi_profiles", ["user_id"])
    op.create_table(
        "rbi_sessions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("profile_id", sa.String(length=64), sa.ForeignKey("rbi_profiles.id"), nullable=False),
        sa.Column("manager_profile_id", sa.String(length=64), nullable=False),
        sa.Column("target_url_encrypted", sa.Text()),
        sa.Column("viewer_token_hash", sa.String(length=128), unique=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("cdp_endpoint_internal", sa.Text()),
        sa.Column("viewer_endpoint_internal", sa.Text()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("stopped_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_rbi_sessions_user_id", "rbi_sessions", ["user_id"])
    op.create_index("ix_rbi_sessions_profile_id", "rbi_sessions", ["profile_id"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_id", sa.String(length=64), sa.ForeignKey("rbi_sessions.id")),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("domain_hash", sa.String(length=128)),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("rbi_sessions")
    op.drop_table("rbi_profiles")
    op.drop_table("users")
