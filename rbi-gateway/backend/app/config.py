from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "change-me"
    token_hash_secret: str = "change-me-token-hash"
    field_encryption_key: str = "change-me-field-key"
    public_base_url: str = "http://localhost"
    manager_base_url: str = "http://cloakbrowser-manager:8080"
    cloak_manager_auth_token: str = "change-me-manager-internal-token"
    database_url: str = "postgresql+psycopg://rbi_gateway:change-me-postgres-password@postgres:5432/rbi_gateway"
    redis_url: str = "redis://redis:6379/0"
    viewer_token_ttl_minutes: int = 60
    session_idle_timeout_minutes: int = 30
    max_running_sessions: int = 20
    max_running_sessions_per_user: int = 3
    allowed_origins: str = "http://localhost"
    log_level: str = "INFO"
    access_log_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
