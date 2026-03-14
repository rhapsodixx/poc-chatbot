"""OpenRouter LLM client with primary/fallback model support.

Implemented in Phase 3.
"""

import httpx
from app.config import get_settings


async def generate_response(
    messages: list[dict],
    *,
    use_fallback: bool = False,
) -> tuple[str, dict]:
    """Send a chat completion request to OpenRouter.

    Args:
        messages: OpenAI-compatible message list.
        use_fallback: If True, use the fallback model instead of primary.

    Returns:
        A tuple of (assistant_reply_text, usage_dict).

    TODO (Phase 3): Implement full request with streaming, error handling,
    and automatic fallback on primary model failure.
    """
    settings = get_settings()
    model = (
        settings.openrouter_fallback_model
        if use_fallback
        else settings.openrouter_primary_model
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"], data.get("usage", {})
