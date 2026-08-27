"""Centralized Gemini client access.

This is the single place that constructs a Gemini SDK client. Application
code should never import `google.genai` directly or hard-code model names -
use `get_gemini_client()` plus the model names on `Settings` (or the thin
wrappers in `app.services.ai_service`) instead.
"""

from functools import lru_cache

from google import genai

from app.core.config import get_settings


@lru_cache
def get_gemini_client() -> genai.Client:
    """Returns a cached Gemini client built from GEMINI_API_KEY.

    Construction never makes a network call, so the application boots fine
    even when no API key is configured yet; the SDK does require a non-empty
    string to construct, so an unset key falls back to a placeholder and
    calls made through the client will only fail once actually invoked.
    """
    settings = get_settings()
    return genai.Client(api_key=settings.gemini_api_key or "unconfigured")
