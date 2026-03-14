"""RAG pipeline — orchestrates the 3-step guardrail retrieval-augmented generation.

This module ties together intent routing, semantic retrieval, confidence checking,
and conditioned generation to produce safe, domain-confined responses.
"""

import logging

from app.config import get_settings
from app.services.llm import generate_response
from app.services.vectorstore import query_similar

logger = logging.getLogger(__name__)

# ── System Prompts ───────────────────────────────────────────

INTENT_CLASSIFICATION_PROMPT = """You are a query classifier for satusatu.com, an attraction and ticketing platform.

Classify whether the following user query is related to:
- Products, attractions, or destinations on satusatu.com
- Ticket purchasing, pricing, or availability
- Itineraries, tours, or trip planning on satusatu.com
- General customer support about satusatu.com services

Reply with EXACTLY one word:
- "RELEVANT" if the query is related to the above topics
- "OFFTOPIC" if the query is unrelated (e.g., politics, coding, recipes, other websites)

User query: {query}"""

GENERATION_SYSTEM_PROMPT = """You are the satusatu.com concierge assistant. Your role is to help customers with attractions, tickets, itineraries, and trip planning.

STRICT RULES:
1. You MUST ONLY use the provided Context to answer the user's question.
2. Do NOT invent products, prices, itineraries, or any information not in the Context.
3. Do NOT recommend competitors or external services.
4. If the Context does not contain enough information to answer the question, you MUST reply with EXACTLY the string: TRIGGER_HANDOFF
5. Be friendly, concise, and helpful.
6. When mentioning products or attractions, include relevant details like pricing if available.
7. Format your response in a clear, readable way.

Context:
{context}"""

OFF_TOPIC_RESPONSE = (
    "I specialize in attractions, tickets, and itineraries for satusatu.com. "
    "How can I help you plan your next adventure with our available experiences? 😊"
)

HANDOFF_MESSAGE = (
    "I don't have enough information to answer that question accurately. "
    "Let me connect you with our support team who can help you directly!"
)


# ── Guardrail 1: Intent Router ───────────────────────────────


async def classify_intent(query: str) -> bool:
    """Classify whether a query is relevant to satusatu.com.

    Returns True if relevant, False if off-topic.
    """
    try:
        prompt = INTENT_CLASSIFICATION_PROMPT.format(query=query)
        result = await generate_response(
            messages=[{"role": "user", "content": prompt}],
        )
        classification = result.strip().upper()
        is_relevant = "RELEVANT" in classification
        logger.info(f"Intent classification: '{classification}' → relevant={is_relevant}")
        return is_relevant
    except Exception as e:
        logger.warning(f"Intent classification failed: {e}, defaulting to relevant")
        return True  # Fail open — let the other guardrails catch it


# ── Guardrail 2: Semantic Confidence ─────────────────────────


async def retrieve_context(query: str) -> tuple[str, float, list[dict]]:
    """Retrieve relevant context from ChromaDB and assess confidence.

    Returns:
        Tuple of (combined_context, best_similarity_score, source_metadata)
    """
    settings = get_settings()

    results = await query_similar(
        query_text=query,
        n_results=settings.max_retrieved_chunks,
    )

    if not results["documents"] or not results["documents"][0]:
        return "", 0.0, []

    documents = results["documents"][0]
    distances = results["distances"][0]  # ChromaDB returns distances (lower = better)
    metadatas = results["metadatas"][0]

    # ChromaDB cosine distance: 0 = identical, 2 = opposite
    # Convert to similarity: 1 - (distance / 2)
    similarities = [1 - (d / 2) for d in distances]
    best_similarity = max(similarities) if similarities else 0.0

    # Combine top documents into context
    context_parts = []
    sources = []
    for doc, sim, meta in zip(documents, similarities, metadatas):
        if sim >= settings.similarity_threshold:
            context_parts.append(doc)
            sources.append(meta)

    combined_context = "\n\n---\n\n".join(context_parts)

    logger.info(
        f"Retrieved {len(context_parts)} relevant chunks "
        f"(best similarity: {best_similarity:.3f}, threshold: {settings.similarity_threshold})"
    )

    return combined_context, best_similarity, sources


# ── Guardrail 3: Conditioned Generation ──────────────────────


async def generate_answer(query: str, context: str) -> str:
    """Generate a response using the LLM with strict domain confinement.

    Returns the LLM response, or 'TRIGGER_HANDOFF' if the model can't answer.
    """
    system_prompt = GENERATION_SYSTEM_PROMPT.format(context=context)

    try:
        response = await generate_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
        )
        return response.strip()
    except Exception as e:
        logger.error(f"Primary LLM failed: {e}, trying fallback")
        try:
            response = await generate_response(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                use_fallback=True,
            )
            return response.strip()
        except Exception as e2:
            logger.error(f"Fallback LLM also failed: {e2}")
            return "TRIGGER_HANDOFF"


# ── Main RAG Pipeline ────────────────────────────────────────


async def process_message(query: str) -> dict:
    """Process a user message through the full 3-step RAG pipeline.

    Returns:
        dict with keys:
            - reply: The bot's response text
            - handoff: None or handoff payload dict
            - sources: List of source metadata dicts
    """
    settings = get_settings()

    # ── Step 1: Intent Routing ──
    is_relevant = await classify_intent(query)
    if not is_relevant:
        logger.info("Query classified as off-topic, returning canned response")
        return {
            "reply": OFF_TOPIC_RESPONSE,
            "handoff": None,
            "sources": [],
        }

    # ── Step 2: Semantic Retrieval + Confidence Check ──
    context, best_score, sources = await retrieve_context(query)

    if not context or best_score < settings.similarity_threshold:
        logger.info(
            f"Low confidence (score={best_score:.3f}), triggering handoff"
        )
        return {
            "reply": HANDOFF_MESSAGE,
            "handoff": {
                "type": "handoff",
                "message": HANDOFF_MESSAGE,
                "freshdesk_url": "https://satusatu.freshdesk.com/support/tickets/new",
                "whatsapp_url": "https://wa.me/628001234567?text=Hi,%20I%20need%20help%20with%20satusatu.com",
            },
            "sources": sources,
        }

    # ── Step 3: Conditioned Generation ──
    answer = await generate_answer(query, context)

    if "TRIGGER_HANDOFF" in answer:
        logger.info("LLM triggered handoff via TRIGGER_HANDOFF keyword")
        return {
            "reply": HANDOFF_MESSAGE,
            "handoff": {
                "type": "handoff",
                "message": HANDOFF_MESSAGE,
                "freshdesk_url": "https://satusatu.freshdesk.com/support/tickets/new",
                "whatsapp_url": "https://wa.me/628001234567?text=Hi,%20I%20need%20help%20with%20satusatu.com",
            },
            "sources": sources,
        }

    return {
        "reply": answer,
        "handoff": None,
        "sources": sources,
    }
