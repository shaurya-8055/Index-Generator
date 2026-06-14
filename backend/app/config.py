"""Application configuration loaded from environment variables.

Sensible defaults let the app run locally without any external services:
the database falls back to SQLite and the LLM falls back to a dependency-free
heuristic extractor when no API key is configured.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- App ----
    app_name: str = "AI Index Generator"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api"

    # ---- Storage ----
    storage_dir: Path = BASE_DIR / "storage"
    max_upload_bytes: int = 50 * 1024 * 1024  # 50 MB

    # ---- Database ----
    database_url: str = f"sqlite:///{(BASE_DIR / 'index_generator.db').as_posix()}"

    # ---- Auth ----
    secret_key: str = "change-me-in-production-please-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 day

    # ---- LLM ----
    # provider: one of "openai", "gemini", "ollama", "fallback"
    llm_provider: str = "fallback"
    llm_model: str = ""  # provider-specific default applied if empty
    llm_temperature: float = 0.0
    openai_api_key: str = ""
    google_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # ---- Text chunking ----
    chunk_size: int = 4000
    chunk_overlap: int = 200

    # ---- Vector DB (optional) ----
    enable_vector_store: bool = False
    chroma_dir: Path = BASE_DIR / "chroma"

    # ---- Rate limiting ----
    rate_limit: str = "60/minute"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
