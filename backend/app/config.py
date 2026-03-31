import os
import secrets
import warnings
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AI Gateway Orchestrator"
    app_version: str = "1.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///data/gateway.db"

    @property
    def async_database_url(self) -> str:
        url = os.getenv("DATABASE_URL", self.database_url)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        elif url.startswith("sqlite://"):
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url

    # Security — set SECRET_KEY env var in production; defaults to ephemeral random key (safe for dev, rotates on restart)
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    def __init__(self, **data):
        super().__init__(**data)
        if not self.secret_key:
            self.secret_key = secrets.token_hex(32)
            if not self.debug:
                warnings.warn(
                    "SECRET_KEY env var not set — using ephemeral random key. "
                    "All JWTs will be invalidated on restart. Set SECRET_KEY in production.",
                    RuntimeWarning,
                    stacklevel=2,
                )
        # Override CORS from env var if set
        env_origins = os.getenv("ALLOWED_ORIGINS", "")
        if env_origins:
            self.allowed_origins = [o.strip() for o in env_origins.split(",") if o.strip()]

    # Anthropic (primary LLM)
    anthropic_api_key: Optional[str] = None

    # Optional LLM providers
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region_name: str = "us-east-1"

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_day: int = 10000

    # CORS — set ALLOWED_ORIGINS env var as comma-separated list in production
    # e.g. ALLOWED_ORIGINS=https://your-app.vercel.app,https://namango.ai
    allowed_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # don't crash on unknown env vars (e.g. NEWSAPI_KEY, custom vars)


settings = Settings()
