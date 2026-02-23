from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 5001
    debug: bool = True
    workers: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> ApiSettings:
    settings = ApiSettings()
    if settings.debug and settings.workers < 1:
        settings.workers = 1
    if not settings.debug and settings.workers < 1:
        settings.workers = 4
    return settings
