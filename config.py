"""Centralised configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            "Copy .env.example → .env and fill in your credentials."
        )
    return value


@dataclass(frozen=True)
class Config:
    # Anthropic
    anthropic_api_key: str

    # HeyGen
    heygen_api_key: str
    heygen_template_id: str   # Template with your avatar pre-configured

    # LinkedIn
    linkedin_client_id: str
    linkedin_client_secret: str
    linkedin_access_token: str
    linkedin_person_urn: str

    # Scheduler
    post_time_utc: str
    videos_per_run: int

    # Content
    content_niche: str
    creator_name: str

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            anthropic_api_key=_require("ANTHROPIC_API_KEY"),
            heygen_api_key=_require("HEYGEN_API_KEY"),
            heygen_template_id=_require("HEYGEN_TEMPLATE_ID"),
            linkedin_client_id=_require("LINKEDIN_CLIENT_ID"),
            linkedin_client_secret=_require("LINKEDIN_CLIENT_SECRET"),
            linkedin_access_token=_require("LINKEDIN_ACCESS_TOKEN"),
            linkedin_person_urn=_require("LINKEDIN_PERSON_URN"),
            post_time_utc=os.getenv("POST_TIME_UTC", "09:00"),
            videos_per_run=int(os.getenv("VIDEOS_PER_RUN", "1")),
            content_niche=os.getenv("CONTENT_NICHE", "AI tools, automation, and building with AI"),
            creator_name=os.getenv("CREATOR_NAME", ""),
        )
