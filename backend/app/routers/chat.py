"""Chat API router — handles user messages through the RAG pipeline.

Endpoints:
    POST /api/chat — Process a user message and return bot response
"""

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.rag import process_message

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""

    message: str
    conversation_id: str | None = None


class HandoffPayload(BaseModel):
    """Payload returned when a human handoff is triggered."""

    type: str = "handoff"
    message: str
    email_url: str | None = None
    whatsapp_url: str | None = None


class ChatResponse(BaseModel):
    """Response sent back to the frontend."""

    reply: str
    conversation_id: str
    handoff: HandoffPayload | None = None
    tokens_used: int | None = None
    cost: float | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Process a user message through the 3-step guardrail RAG pipeline.

    Steps:
      1. Intent routing — off-topic queries get a polite redirect
      2. Semantic retrieval — finds relevant knowledge chunks
      3. Conditioned generation — LLM answers from context only
    """
    conversation_id = req.conversation_id or str(uuid.uuid4())

    result = await process_message(req.message)

    handoff = None
    if result["handoff"]:
        handoff = HandoffPayload(**result["handoff"])

    return ChatResponse(
        reply=result["reply"],
        conversation_id=conversation_id,
        handoff=handoff,
        tokens_used=result.get("tokens_used", 0),
        cost=result.get("cost", 0.0),
    )
