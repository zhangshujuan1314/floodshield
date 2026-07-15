import logging
import warnings

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://floodshield:floodshield@localhost:5432/floodshield"
    MOCK_MODE: bool = True
    AI_PROVIDER: str = "noop"
    MAP_PROVIDER: str = "mock"
    WEATHER_PROVIDER: str = "mock"
    NOTIFICATION_PROVIDER: str = "mock"
    SECRET_KEY: str = "dev-secret-change-in-production"
    API_PREFIX: str = "/v1"
    INTERNAL_PREFIX: str = "/internal"
    ALLOWED_ORIGINS: list[str] = ["*"]


settings = Settings()

if not settings.MOCK_MODE and "*" in settings.ALLOWED_ORIGINS:
    warnings.warn(
        "ALLOWED_ORIGINS contains '*' in production mode. "
        "Set ALLOWED_ORIGINS to explicit origins for security.",
        stacklevel=2,
    )
    logger.warning(
        "ALLOWED_ORIGINS contains '*' in production mode. "
        "Set ALLOWED_ORIGINS to explicit origins for security."
    )
