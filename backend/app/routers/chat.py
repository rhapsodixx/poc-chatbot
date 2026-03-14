"""Chat API router — handles user messages and returns bot responses.

Implemented in Phase 3.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""

    message: str
    conversation_id: str | None = None


class HandoffPayload(BaseModel):
    """Payload returned when a human handoff is triggered."""

    type: str = "handoff"
    message: str
    freshdesk_url: str | None = None
    whatsapp_url: str | None = None


class ChatResponse(BaseModel):
    """Response sent back to the frontend."""

    reply: str
    conversation_id: str
    handoff: HandoffPayload | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Process a user message through the RAG pipeline.

    TODO (Phase 3):
      1. Intent routing (guardrail 1)
      2. Semantic retrieval from ChromaDB
      3. Confidence check (guardrail 2)
      4. Conditioned generation via OpenRouter (guardrail 3)
    """
    return ChatResponse(
        reply="👋 Hello! I'm the satusatu.com assistant. I'm under construction — check back soon!",
        conversation_id=req.conversation_id or "demo-session",
    )
