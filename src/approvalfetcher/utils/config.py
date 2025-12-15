from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    infura_api_key: str = Field(..., min_length=1)
    infura_endpoint: str = "https://mainnet.infura.io/v3/"

    blocks_per_chunk: int = 10000
    max_concurrent_chunks: int = 5

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator('infura_api_key')
    @classmethod
    def validate_infura_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(
                "Infura API key is required. "
                "Please set INFURA_API_KEY in your .env file. "
                "Get a free API key at: https://infura.io/"
            )
        return v.strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
