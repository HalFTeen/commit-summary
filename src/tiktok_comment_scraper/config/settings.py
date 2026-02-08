"""Application configuration using pydantic-settings."""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ZAI_API_KEY: str
    ZAI_BASE_URL: str = "https://api.z.ai/api/paas/v4/"
    ZAI_MODEL: str = "glm-4.7"
    ZAI_TIMEOUT: int = 300
    ZAI_MAX_RETRIES: int = 3

    FALLBACK_PROVIDERS: List[str] = []
    ENABLE_FALLBACK: bool = True

    TIKTOK_TIMEOUT: int = 30
    TIKTOK_MAX_RETRIES: int = 5
    TIKTOK_REQUEST_DELAY: float = 1.0

    USER_AGENT: Optional[str] = None
    PROXY_URL: Optional[str] = None

    OUTPUT_DIR: str = "output"
    BATCH_SIZE: int = 50

    class Config:
        """Pydantic config."""
        env_prefix = ""


settings = Settings()
