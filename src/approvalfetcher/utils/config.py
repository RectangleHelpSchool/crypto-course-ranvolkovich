from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # API Key (required)
    infura_api_key: str = ""

    # Endpoint
    infura_endpoint: str = "https://mainnet.infura.io/v3/"

    # Block Scanning Configuration
    blocks_per_chunk: int = 10000
    max_concurrent_chunks: int = 5

    # Retry Configuration
    max_retry_attempts: int = 5
    retry_min_wait: int = 1
    retry_max_wait: int = 60
    retry_multiplier: int = 2

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
