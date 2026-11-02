from functools import lru_cache

from django.conf import settings
from openai import OpenAI

from .exceptions import LlmNotConfigured


def is_configured() -> bool:
    return bool(settings.AI_MODEL and (settings.AI_API_KEY or settings.AI_BASE_URL))


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    """Single OpenAI-compatible client; transport-level retries (429/5xx/network) are done by the SDK."""
    if not is_configured():
        raise LlmNotConfigured("LLM is not configured: set AI_MODEL and AI_API_KEY (and AI_BASE_URL if not OpenAI)")
    return OpenAI(
        base_url=settings.AI_BASE_URL,
        api_key=settings.AI_API_KEY or "not-needed",
        timeout=settings.AI_TIMEOUT_S,
        max_retries=1,
    )
