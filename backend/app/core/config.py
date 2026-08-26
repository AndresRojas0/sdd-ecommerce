"""Application settings loaded from environment variables (.env in dev)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://punto:punto@db:5432/punto"

    # JWT per audience (ADR-003): store and admin are fully isolated.
    jwt_secret_store: str = "change-me-store"
    jwt_secret_admin: str = "change-me-admin"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # Visit deduplication window in hours (RN-08 / ADR-001)
    visit_dedup_window_hours: int = 24

    # CORS origins, comma-separated: CORS_ORIGINS=http://localhost:3000,...
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Admin bootstrap (ADR-006): ADMIN_INITIAL_USER holds the email.
    admin_initial_user: str | None = None
    admin_initial_password: str | None = None
    admin_initial_display_name: str | None = None

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
