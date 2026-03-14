"""RAG pipeline — orchestrates the 3-step guardrail retrieval-augmented generation.

This module ties together intent routing, semantic retrieval, confidence checking,
and conditioned generation to produce safe, domain-confined responses.
"""

import logging
import random

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
- "RELEVANT" if the query is related to general products, tickets, or support.
- "ITINERARY" if the user is explicitly asking for a trip itinerary, a day-by-day plan, or suggesting a travel schedule.
- "OFFTOPIC" if the query is unrelated (e.g., politics, coding, recipes, other websites)

User query: {query}"""

ITINERARY_SYSTEM_PROMPT = """You are the satusatu.com itinerary planner. Your role is to help customers plan their trips using ONLY attractions and products available on satusatu.com.

STRICT RULES for Itineraries:
1. You MUST ONLY use the provided Context to build the itinerary. Do NOT hallucinate or invent products, attractions, or locations not present in the Context.
2. The itinerary MUST NOT exceed 3 days. If the user explicitly asks for an itinerary longer than 3 days (e.g., 4 days, 5 days), you MUST NOT output the JSON block. Instead, reply with a natural, friendly apology stating that you currently can only generate itineraries for a maximum of 3 days. Provide varied and natural-sounding responses.
3. Be realistic about timing:
   - Estimate the duration for each activity based on the nature of the product.
   - You MUST account for realistic commute/travel times between consecutive locations.
4. If the Context does not contain enough information to create a meaningful itinerary, you MUST reply with EXACTLY the string: TRIGGER_HANDOFF
5. TAG EXTRACTION: As you evaluate each product for the itinerary activities, explicitly extract and assign relevant tags to it. 
   - For "locally curated": You MUST ONLY assign this tag if the product's Context contains the EXACT string "locally curated".
   - For "kids friendly", "family friendly", or "pets friendly": Assign these tags if the product mentions or fits those specific criteria.
6. FORMATTING ITINERARY SUGGESTIONS: You MUST output a structured JSON block at the very end of your response wrapped in ```json tags.
   - Text portion: Write a short, friendly preamble (e.g., "Here is a suggested itinerary for your trip:"). Do NOT mention specific products or schedules in this text portion! Do NOT use bullet points in the text portion!
   - JSON portion: You MUST include the JSON block populated with the itinerary details.
   The JSON must follow this exact schema:
   {{
     "itinerary": [
       {{
         "day": 1,
         "title": "Day 1 Title",
         "activities": [
           {{
             "time": "09:00 - 13:00",
             "title": "Activity Title",
             "description": "Short description of what to do.",
             "products": [
               {{
                 "imageUrl": "Image URL mapped EXACTLY from the [Image URL: ...] tag in the context chunk. If none, leave empty string",
                 "location": "Location Name",
                 "title": "Full product title",
                 "rating": "4.9",
                 "reviewsCount": "100+",
                 "soldCount": "500+",
                 "priceOptions": {{
                   "original": "IDR 950,000",
                   "current": "IDR 350,000",
                   "discountBadge": "-63%"
                 }},
                 "productUrl": "Target URL mapped EXACTLY from the [Source URL: ...] tag in the context chunk",
                 "tags": ["extracted tag 1", "extracted tag 2"]
               }}
             ]
           }}
         ]
       }}
     ]
   }}

Context:
{context}"""

GENERATION_SYSTEM_PROMPT = """You are the satusatu.com concierge assistant. Your role is to help customers with attractions, tickets, itineraries, and trip planning.

STRICT RULES:
1. You MUST ONLY use the provided Context to answer the user's question.
2. Do NOT invent products, prices, itineraries, or any information not in the Context.
3. Do NOT recommend competitors or external services.
4. If the Context does not contain enough information to answer the question, you MUST reply with EXACTLY the string: TRIGGER_HANDOFF
5. Be friendly, concise, and helpful.
6. When mentioning products or attractions, include relevant details like pricing if available.
7. PRIORITY RULE: If the user asks for "unique", "best", "recommended" attractions, or similar subjective inquiries, you MUST prioritize and suggest the products with the highest `rating` AND the highest `soldCount` from the provided Context.
8. MINIMUM SOLD THRESHOLD: You MUST NOT suggest highly-rated products if their `soldCount` is very low (specifically, less than 100 units sold). High ratings must be backed by a minimum sales volume to be considered a top recommendation.

KEYWORD MATCHING & COMPREHENSIVE RECOMMENDATIONS:
9. If the user query implies specific categories like "kids friendly", "family friendly", or "pets friendly", you MUST return ALL products from the Context that match these categories. Do NOT limit your recommendations to just 1 or 2 products if more valid matches are available in the Context.
10. TAG EXTRACTION: As you evaluate each product, explicitly extract and assign relevant tags to it. 
    - For "locally curated": You MUST ONLY assign this tag if the product's Context contains the EXACT string "locally curated".
    - For "kids friendly", "family friendly", or "pets friendly": Assign these tags if the product mentions or fits those specific criteria.

FORMATTING PRODUCT SUGGESTIONS: 
11. If the context contains products or tickets, you MUST output a structured JSON block at the very end of your response wrapped in ```json tags containing the items.
   - Text portion: Write a short, friendly, and conversational preamble (e.g., "Here are some top-rated tickets you might like for your trip:"). Do NOT mention specific product titles, prices, or ratings in this text portion! Do NOT use bullet points in the text portion!
   - JSON portion: You MUST include the JSON block populated with the product details.
   The JSON must follow this exact schema:
   {{
     "products": [
       {{
         "imageUrl": "Image URL mapped EXACTLY from the [Image URL: ...] tag in the context chunk. If none, leave empty string",
         "location": "Location Name, City, Bali",
         "title": "Full product title",
         "rating": "4.9",
         "reviewsCount": "100+",
         "soldCount": "500+",
         "priceOptions": {{
           "original": "IDR 950,000",
           "current": "IDR 350,000",
           "discountBadge": "-63%"
         }},
         "productUrl": "Target URL mapped EXACTLY from the [Source URL: ...] tag in the context chunk",
         "tags": ["extracted tag 1", "extracted tag 2"]
       }}
     ]
   }}

Context:
{context}"""

OFF_TOPIC_RESPONSE = (
    "I specialize in attractions, tickets, and itineraries for satusatu.com. "
    "How can I help you plan your next adventure with our available experiences? 😊"
)

HANDOFF_MESSAGES = [
    "I'm not completely sure about that. Let me connect you with our support team who can help you right away!",
    "That's a great question! I don't have the exact details, but our support team will be happy to assist you.",
    "I don't have enough information to answer that accurately. Let me hand this over to a human agent who can help.",
    "To make sure you get the best answer, I'm going to connect you with our support team.",
    "I'm still learning, so I'll pass this question to our support team who can give you a precise answer."
]


# ── Guardrail 1: Intent Router ───────────────────────────────


async def classify_intent(query: str) -> str:
    """Classify whether a query is relevant to satusatu.com, an itinerary, or off-topic.

    Returns "RELEVANT", "ITINERARY", or "OFFTOPIC".
    """
    try:
        prompt = INTENT_CLASSIFICATION_PROMPT.format(query=query)
        result, _ = await generate_response(
            messages=[{"role": "user", "content": prompt}],
        )
        classification = result.strip().upper()
        if "ITINERARY" in classification:
            intent = "ITINERARY"
        elif "RELEVANT" in classification:
            intent = "RELEVANT"
        else:
            intent = "OFFTOPIC"
        logger.info(f"Intent classification: '{classification}' → {intent}")
        return intent
    except Exception as e:
        logger.warning(f"Intent classification failed: {e}, defaulting to RELEVANT")
        return "RELEVANT"  # Fail open — let the other guardrails catch it


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
            url = meta.get("url", "")
            img_url = meta.get("image_url", "")
            title = meta.get("title", "")
            
            chunk_text = f"[Source URL: {url}]\n[Image URL: {img_url}]\n[Title: {title}]\n{doc}"
            context_parts.append(chunk_text)
            sources.append(meta)

    combined_context = "\n\n---\n\n".join(context_parts)

    logger.info(
        f"Retrieved {len(context_parts)} relevant chunks "
        f"(best similarity: {best_similarity:.3f}, threshold: {settings.similarity_threshold})"
    )

    return combined_context, best_similarity, sources


# ── Guardrail 3: Conditioned Generation ──────────────────────


async def generate_answer(query: str, context: str, intent: str = "RELEVANT") -> tuple[str, dict]:
    """Generate a response using the LLM with strict domain confinement.

    Returns a tuple of (LLM_response, token_usage_dict).
    """
    if intent == "ITINERARY":
        system_prompt = ITINERARY_SYSTEM_PROMPT.format(context=context)
    else:
        system_prompt = GENERATION_SYSTEM_PROMPT.format(context=context)

    try:
        response, usage = await generate_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
        )
        return response.strip(), usage
    except Exception as e:
        logger.error(f"Primary LLM failed: {e}, trying fallback")
        try:
            response, usage = await generate_response(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                use_fallback=True,
            )
            return response.strip(), usage
        except Exception as e2:
            logger.error(f"Fallback LLM also failed: {e2}")
            return "TRIGGER_HANDOFF", {}


# ── Main RAG Pipeline ────────────────────────────────────────


async def process_message(query: str) -> dict:
    """Process a user message through the full 3-step RAG pipeline.

    Returns:
        dict with keys:
            - reply: The bot's response text
            - handoff: None or handoff payload dict
            - sources: List of source metadata dicts
            - tokens_used: Total tokens consumed (int)
            - cost: Estimated cost (float)
    """
    settings = get_settings()

    # ── Step 1: Intent Routing ──
    intent = await classify_intent(query)
    if intent == "OFFTOPIC":
        logger.info("Query classified as off-topic, returning canned response")
        return {
            "reply": OFF_TOPIC_RESPONSE,
            "handoff": None,
            "sources": [],
            "tokens_used": 0,
            "cost": 0.0,
        }

    # ── Step 2: Semantic Retrieval + Confidence Check ──
    context, best_score, sources = await retrieve_context(query)

    if not context or best_score < settings.similarity_threshold:
        logger.info(
            f"Low confidence (score={best_score:.3f}), triggering handoff"
        )
        return {
            "reply": random.choice(HANDOFF_MESSAGES),
            "handoff": {
                "type": "handoff",
                "message": random.choice(HANDOFF_MESSAGES),
                "email_url": "mailto:support@satusatu.com",
                "whatsapp_url": "https://wa.me/628001234567?text=Hi,%20I%20need%20help%20with%20satusatu.com",
            },
            "sources": sources,
            "tokens_used": 0,
            "cost": 0.0,
        }

    # ── Step 3: Conditioned Generation ──
    answer, usage = await generate_answer(query, context, intent)

    # Calculate cost roughly based on common models
    # We use a fallback cost calculation here
    model_name = settings.openrouter_primary_model
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
    
    cost = 0.0
    if "gemini-flash" in model_name:
        cost = (prompt_tokens / 1_000_000 * 0.075) + (completion_tokens / 1_000_000 * 0.3)
    elif "gpt-4o-mini" in model_name:
        cost = (prompt_tokens / 1_000_000 * 0.15) + (completion_tokens / 1_000_000 * 0.6)
    else:
        # Generic fallback
        cost = (prompt_tokens / 1_000_000 * 0.1) + (completion_tokens / 1_000_000 * 0.5)

    if "TRIGGER_HANDOFF" in answer:
        logger.info("LLM triggered handoff via TRIGGER_HANDOFF keyword")
        return {
            "reply": random.choice(HANDOFF_MESSAGES),
            "handoff": {
                "type": "handoff",
                "message": random.choice(HANDOFF_MESSAGES),
                "email_url": "mailto:support@satusatu.com",
                "whatsapp_url": "https://wa.me/6287878111111?text=Hi,%20I%20need%20help%20with%20satusatu.com",
            },
            "sources": sources,
            "tokens_used": total_tokens,
            "cost": cost,
        }

    return {
        "reply": answer,
        "handoff": None,
        "sources": sources,
        "tokens_used": total_tokens,
        "cost": cost,
    }
