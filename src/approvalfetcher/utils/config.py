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

    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    coingecko_api_key: str = Field(default="")

    max_concurrent_tasks: int = Field(default=2, description="Maximum concurrent API tasks")

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
