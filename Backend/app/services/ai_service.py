"""Reusable Gemini service foundation.

Thin wrappers over the centralized client from `app.core.gemini`. This is
foundation only for later phases (complaint triage, evidence analysis, RAG,
inspector assistant, etc.) - no agent logic, tool orchestration, OCR, or
vision analysis lives here yet.

All Gemini SDK exceptions are normalized to the app's own `AppError`
subclasses here so that callers (agents/services) never need to import or
handle `google.genai.errors` directly - this is the one place API failures,
timeouts, and rate limits are translated into a small, stable error set.
"""

import logging

from google.genai import errors as genai_errors
from google.genai import types

from app.core.config import get_settings
from app.core.gemini import get_gemini_client
from app.utils.exceptions import GeminiRateLimitedError, GeminiRequestError, GeminiUnavailableError

logger = logging.getLogger(__name__)


def generate_text(prompt: str, *, use_reasoning_model: bool = False) -> str:
    """Generates a single text completion using the configured Gemini model."""
    settings = get_settings()
    client = get_gemini_client()
    model = settings.gemini_reasoning_model if use_reasoning_model else settings.gemini_main_model
    config = types.GenerateContentConfig(http_options=_http_options(settings))
    response = _generate(client, model, prompt, config=config)
    return response.text


def generate_structured_json(prompt: str, *, response_schema: dict, use_reasoning_model: bool = False) -> str:
    """Generates a single JSON completion constrained to the given JSON
    schema (see https://ai.google.dev/gemini-api/docs/structured-output).

    Returns the raw JSON text; callers are responsible for parsing and
    validating it against their own Pydantic model (see
    app.agents.complaint_triage.agent for an example) - this function
    only talks to Gemini and does not assume the shape of any specific
    agent's output.
    """
    settings = get_settings()
    client = get_gemini_client()
    model = settings.gemini_reasoning_model if use_reasoning_model else settings.gemini_main_model
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_schema,
        http_options=_http_options(settings),
    )
    response = _generate(client, model, prompt, config=config)
    if not response.text:
        raise GeminiRequestError("The AI service returned an empty response.")
    return response.text


def generate_structured_json_with_media(
    prompt: str,
    *,
    media_bytes: bytes,
    media_mime_type: str,
    response_schema: dict,
    use_reasoning_model: bool = False,
) -> str:
    """Same contract as generate_structured_json, but sends inline media (image/PDF
    bytes) alongside the prompt for Gemini multimodal analysis (see
    app.agents.evidence_analysis.agent for an example). Returns the raw JSON text;
    callers validate it against their own Pydantic model.
    """
    settings = get_settings()
    client = get_gemini_client()
    model = settings.gemini_reasoning_model if use_reasoning_model else settings.gemini_main_model
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_schema,
        http_options=_http_options(settings),
    )
    contents = [types.Part.from_bytes(data=media_bytes, mime_type=media_mime_type), prompt]
    response = _generate(client, model, contents, config=config)
    if not response.text:
        raise GeminiRequestError("The AI service returned an empty response.")
    return response.text


def embed_text(text: str) -> list[float]:
    """Returns an embedding vector for the given text using the configured embedding
    model, truncated/normalized to `settings.gemini_embedding_dimensions` so every
    vector stored in `rag_document_chunks.embedding` has a consistent size (required
    by the pgvector column - see app/core/vector_types.py)."""
    settings = get_settings()
    client = get_gemini_client()
    config = types.EmbedContentConfig(output_dimensionality=settings.gemini_embedding_dimensions)
    try:
        response = client.models.embed_content(model=settings.gemini_embedding_model, contents=text, config=config)
    except genai_errors.APIError as exc:
        raise _normalize_api_error(exc) from exc
    except Exception as exc:  # transport-level failures (timeouts, connection errors, ...)
        raise GeminiUnavailableError("The AI service did not respond in time.") from exc
    return list(response.embeddings[0].values)


def _http_options(settings) -> "types.HttpOptions":
    return types.HttpOptions(timeout=int(settings.gemini_request_timeout_seconds * 1000))


def _generate(client, model: str, contents: str | list, *, config: "types.GenerateContentConfig"):
    try:
        return client.models.generate_content(model=model, contents=contents, config=config)
    except genai_errors.APIError as exc:
        raise _normalize_api_error(exc) from exc
    except Exception as exc:  # transport-level failures (timeouts, connection errors, ...)
        raise GeminiUnavailableError("The AI service did not respond in time.") from exc


def _normalize_api_error(exc: "genai_errors.APIError") -> Exception:
    if exc.code == 429:
        return GeminiRateLimitedError()
    if isinstance(exc, genai_errors.ServerError):
        return GeminiUnavailableError()
    # exc.message is vendor-generated text (safety-filter details, schema
    # complaints, key/config state, ...) that we don't want to surface
    # verbatim to an API client - it's logged here for operators instead.
    # See docs/SECURITY_AND_RBAC.md section 11 ("safe error handling").
    logger.warning("Gemini request rejected (code=%s): %s", exc.code, exc.message)
    return GeminiRequestError()
