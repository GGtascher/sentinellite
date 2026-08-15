from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SentinelLite"
    version: str = "0.1.0"
    database_url: str = "sqlite:///./sentinellite.db"
    api_cors_origins: list[str] | str = ["http://localhost:3000"]
    max_upload_bytes: int = 10 * 1024 * 1024
    max_event_chars: int = 256 * 1024
    max_batch_events: int = 5_000
    log_level: str = "INFO"
    rules_path: Path = Path(__file__).resolve().parents[2] / "rules"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("api_cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
