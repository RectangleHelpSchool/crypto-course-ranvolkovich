from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    infura_api_key: str = Field(default="", min_length=1)
    infura_endpoint: str = "https://mainnet.infura.io/v3/"

    blocks_per_chunk: int = 10000
    max_concurrent_chunks: int = 5

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
