import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AI Gateway Orchestrator"
    app_version: str = "1.0.0"
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

    # Security
    secret_key: str = "change-me-in-production-use-random-256-bit-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

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

    # CORS
    allowed_origins: list[str] = ["*", "https://frontend-five-theta-69.vercel.app"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
