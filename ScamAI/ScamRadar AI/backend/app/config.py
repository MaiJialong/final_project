"""Application configuration loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Database
    database_url: str = (
        "postgresql+psycopg://scamradar:scamradar@localhost:5432/scamradar"
    )

    # MiniMax
    minimax_api_key: str = "sk-replace-me"
    minimax_base_url: str = "https://api.minimax.io/v1"
    minimax_chat_model: str = "MiniMax-M3"
    minimax_image_model: str = "image-01"
    minimax_embed_model: str = "embo-01"

    embedding_dim: int = 1536
    asset_output_dir: str = "./generated_assets"

    # When true, network calls to MiniMax are replaced by deterministic stubs.
    offline_mode: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
