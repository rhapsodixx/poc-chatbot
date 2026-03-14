"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Central configuration for the satusatu chatbot backend.

    All values can be overridden via environment variables or a .env file.
    """

    # --- Application ---
    app_name: str = "satusatu-chatbot"
    debug: bool

    # --- OpenRouter LLM ---
    openrouter_api_key: str
    openrouter_base_url: str
    openrouter_primary_model: str
    openrouter_fallback_model: str

    # --- ChromaDB ---
    chroma_host: str
    chroma_port: int
    chroma_collection_name: str

    # --- Ingestion ---
    site_url: str
    sitemap_url: str

    # --- Guardrails ---
    similarity_threshold: float
    max_retrieved_chunks: int

    # --- CORS ---
    cors_origins: list[str]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
