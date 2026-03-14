"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Central configuration for the satusatu chatbot backend.

    All values can be overridden via environment variables or a .env file.
    """

    # --- Application ---
    app_name: str = "satusatu-chatbot"
    debug: bool = False

    # --- OpenRouter LLM ---
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_primary_model: str = "google/gemini-flash-1.5"
    openrouter_fallback_model: str = "openai/gpt-4o-mini"

    # --- ChromaDB ---
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    chroma_collection_name: str = "satusatu_knowledge"

    # --- Ingestion ---
    site_url: str = "https://satusatu.com"
    sitemap_url: str = "https://satusatu.com/sitemap.xml"

    # --- Guardrails ---
    similarity_threshold: float = 0.35
    max_retrieved_chunks: int = 5

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
