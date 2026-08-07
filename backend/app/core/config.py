from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "local"
    app_name: str = "CertifyLK API"
    api_version: str = "1.0.0"
    release_sha: str = Field(default="unknown")
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://certifylk:certifylk@localhost:5432/certifylk"
    cors_origins: list[str] | str = Field(default_factory=lambda: ["http://localhost:3000"])
    upload_dir: Path = Path("./data/uploads")
    max_image_mb: int = 8
    max_pdf_mb: int = 12
    ai_provider: Literal["mock", "gemini"] = "mock"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    gemini_timeout_seconds: float = Field(default=30.0, ge=5.0, le=120.0)
    gemini_temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    gemini_max_output_tokens: int = Field(default=2048, ge=256, le=8192)
    allow_ai_fallback: bool = True
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value

    @field_validator("upload_dir", mode="after")
    @classmethod
    def resolve_upload_dir(cls, value: Path) -> Path:
        return value if value.is_absolute() else BACKEND_ROOT / value


@lru_cache
def get_settings() -> Settings:
    return Settings()
