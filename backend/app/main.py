"""satusatu.com RAG Chatbot — FastAPI Application Entry Point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import chat, ingest


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    settings = get_settings()
    print(f"🚀 {settings.app_name} starting up …")
    print(f"   ChromaDB → {settings.chroma_host}:{settings.chroma_port}")
    print(f"   Primary LLM → {settings.openrouter_primary_model}")
    yield
    print("👋 Shutting down …")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="satusatu Chatbot API",
        description="RAG-based customer support chatbot for satusatu.com",
        version="0.1.0",
        lifespan=lifespan,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers ---
    app.include_router(chat.router, prefix="/api")
    app.include_router(ingest.router, prefix="/api")

    # --- Health check ---
    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
