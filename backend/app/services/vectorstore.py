"""ChromaDB vector store client for semantic retrieval.

Implemented in Phase 2 (ingestion) and Phase 3 (query).
"""

import chromadb
from app.config import get_settings


def get_chroma_client() -> chromadb.HttpClient:
    """Return an HTTP client connected to the ChromaDB container."""
    settings = get_settings()
    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
    )


def get_collection(client: chromadb.HttpClient | None = None):
    """Get or create the knowledge-base collection.

    Args:
        client: Optional pre-existing client. Created if not provided.

    Returns:
        A ChromaDB Collection instance.
    """
    if client is None:
        client = get_chroma_client()
    settings = get_settings()
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},
    )


async def query_similar(
    query_text: str,
    n_results: int = 5,
) -> dict:
    """Search for the most semantically similar chunks.

    Args:
        query_text: The user's query string.
        n_results: Number of results to return.

    Returns:
        ChromaDB query result dict with documents, distances, and metadatas.

    TODO (Phase 3): Use embedding model for query embedding instead of
    ChromaDB's default.
    """
    collection = get_collection()
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
    )
    return results
