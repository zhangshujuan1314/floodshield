import logging
import warnings

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://floodshield:floodshield@localhost:5432/floodshield"
    MOCK_MODE: bool = False
    AI_PROVIDER: str = "noop"
    MAP_PROVIDER: str = "mock"
    MAP_API_KEY: str = ""
    MAP_API_URL: str = "https://restapi.amap.com"
    WEATHER_PROVIDER: str = "mock"
    WEATHER_API_KEY: str = ""
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5"
    NOTIFICATION_PROVIDER: str = "mock"
    SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    API_PREFIX: str = "/v1"
    INTERNAL_PREFIX: str = "/internal"
    ALLOWED_ORIGINS: list[str] = ["*"]

    # Real notification provider settings
    SMS_API_KEY: str = ""
    SMS_API_SECRET: str = ""
    NOTIFICATION_API_URL: str = ""

    # Real AI provider settings
    AI_API_KEY: str = ""
    AI_MODEL: str = "qwen-turbo"
    AI_API_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if not self.MOCK_MODE and self.SECRET_KEY == "dev-secret-change-in-production":
            raise ValueError(
                "SECRET_KEY must be set via environment variable in production mode. "
                "Set MOCK_MODE=true for development, or provide a real SECRET_KEY."
            )
        return self


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
