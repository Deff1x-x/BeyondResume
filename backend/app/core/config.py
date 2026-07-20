from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> parents[2] == backend/, parents[3] == repo root
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[3]


def _env_files() -> tuple[str, ...]:
    candidates = (
        _REPO_ROOT / ".env",
        _BACKEND_DIR / ".env",
        Path(".env"),
    )
    return tuple(str(path) for path in candidates if path.is_file())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files() or (".env",),
        env_file_encoding="utf-8",
        # Root .env also holds frontend/LLM keys unused by the backend Settings model.
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://ebh:ebh@postgres:5432/ebh"
    demo_mode: bool = True
    jwt_secret: str = ""
    jwt_access_ttl_minutes: int = 15
    upload_dir: str = "/app/data/uploads"
    resume_parse_timeout_seconds: int = 20
    github_provider: Literal["demo", "live"] = "live"
    github_token: str = ""
    github_api_timeout_seconds: int = 20
    llm_provider: Literal["mock", "openai"] = "mock"
    llm_api_key: str = ""
    llm_model: str = "gpt-5-mini"
    llm_timeout_seconds: int = 20


settings = Settings()
