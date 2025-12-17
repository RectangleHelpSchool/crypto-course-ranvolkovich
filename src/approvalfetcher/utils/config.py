from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# Find project root (where .env is located)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    infura_api_key: str = Field(default="", min_length=1)
    infura_endpoint: str = "https://mainnet.infura.io/v3/"

    blocks_per_chunk: int = 10000
    max_concurrent_chunks: int = 5
    max_concurrent_tasks: int = Field(default=2, description="Maximum concurrent API tasks")
    request_timeout_seconds: int = Field(default=30, description="Request timeout in seconds")

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
