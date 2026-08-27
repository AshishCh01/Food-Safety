"""Reusable Gemini service foundation.

Thin wrappers over the centralized client from `app.core.gemini`. This is
foundation only for later phases (complaint triage, evidence analysis, RAG,
inspector assistant, etc.) - no agent logic, tool orchestration, OCR, or
vision analysis lives here yet.
"""

from app.core.config import get_settings
from app.core.gemini import get_gemini_client


def generate_text(prompt: str, *, use_reasoning_model: bool = False) -> str:
    """Generates a single text completion using the configured Gemini model."""
    settings = get_settings()
    client = get_gemini_client()
    model = settings.gemini_reasoning_model if use_reasoning_model else settings.gemini_main_model
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text


def embed_text(text: str) -> list[float]:
    """Returns an embedding vector for the given text using the configured embedding model."""
    settings = get_settings()
    client = get_gemini_client()
    response = client.models.embed_content(model=settings.gemini_embedding_model, contents=text)
    return list(response.embeddings[0].values)
