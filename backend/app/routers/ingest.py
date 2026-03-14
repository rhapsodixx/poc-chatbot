"""Ingestion API router — triggers and monitors the data ingestion pipeline."""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from app.ingestion.pipeline import run_ingestion

router = APIRouter(tags=["ingestion"])

# Simple in-memory status tracker
_ingestion_status: dict = {"status": "idle", "last_result": None}


class IngestRequest(BaseModel):
    """Optional overrides for the ingestion pipeline."""

    sitemap_url: str | None = None
    max_concurrent: int = 5


class IngestStatusResponse(BaseModel):
    """Current status of the ingestion pipeline."""

    status: str
    last_result: dict | None = None


async def _run_ingestion_task(sitemap_url: str | None, max_concurrent: int):
    """Background task wrapper for the ingestion pipeline."""
    global _ingestion_status
    _ingestion_status["status"] = "running"
    try:
        result = await run_ingestion(
            sitemap_url=sitemap_url,
            max_concurrent=max_concurrent,
        )
        _ingestion_status["status"] = "completed"
        _ingestion_status["last_result"] = result
    except Exception as e:
        _ingestion_status["status"] = "failed"
        _ingestion_status["last_result"] = {"error": str(e)}


@router.post("/ingest", response_model=IngestStatusResponse)
async def trigger_ingestion(req: IngestRequest, background_tasks: BackgroundTasks):
    """Trigger the ingestion pipeline as a background task.

    Returns immediately with status 'running'. Use GET /api/ingest/status
    to poll for completion.
    """
    if _ingestion_status["status"] == "running":
        return IngestStatusResponse(
            status="already_running",
            last_result=_ingestion_status["last_result"],
        )

    background_tasks.add_task(
        _run_ingestion_task, req.sitemap_url, req.max_concurrent
    )

    return IngestStatusResponse(status="started")


@router.get("/ingest/status", response_model=IngestStatusResponse)
async def get_ingestion_status():
    """Check the current status of the ingestion pipeline."""
    return IngestStatusResponse(
        status=_ingestion_status["status"],
        last_result=_ingestion_status["last_result"],
    )
