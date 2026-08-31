"""Thin wrapper around the Supabase Storage REST API.

Uses the service-role key so uploads/signed URLs work against private
buckets; this key must never be shipped to the frontend. All network calls
are isolated behind `upload_file`/`create_signed_url` so callers (and tests)
can monkeypatch them without hitting the network.
"""

from functools import lru_cache

import httpx

from app.core.config import get_settings
from app.utils.exceptions import EvidenceDownloadError, EvidenceUploadError


@lru_cache
def _client() -> httpx.Client:
    """A single shared, connection-pooling client rather than a new
    connection per call - every upload/download/sign operation otherwise
    paid a fresh TCP+TLS handshake to Supabase Storage on every request."""
    return httpx.Client(timeout=30.0)


def _headers() -> dict[str, str]:
    settings = get_settings()
    key = settings.supabase_service_role_key.get_secret_value()
    return {
        "Authorization": f"Bearer {key}",
        "apikey": key,
    }


def upload_file(bucket: str, path: str, content: bytes, content_type: str) -> str:
    settings = get_settings()
    url = f"{settings.supabase_url}/storage/v1/object/{bucket}/{path}"
    response = _client().post(
        url,
        content=content,
        headers={**_headers(), "Content-Type": content_type},
        timeout=30.0,
    )
    if response.status_code not in (200, 201):
        raise EvidenceUploadError(f"Storage upload failed with status {response.status_code}.")
    return path


def delete_file(bucket: str, path: str) -> None:
    """Best-effort delete of a storage object - callers should not fail an
    otherwise-successful operation (e.g. deleting a document record) just
    because the underlying file was already missing or the delete itself
    failed; the object being gone is the desired end state either way."""
    settings = get_settings()
    url = f"{settings.supabase_url}/storage/v1/object/{bucket}/{path}"
    try:
        _client().request("DELETE", url, headers=_headers(), timeout=30.0)
    except httpx.HTTPError:
        pass


def download_file(bucket: str, path: str) -> bytes:
    """Fetches the raw bytes of an already-uploaded object, e.g. so an AI agent
    can pass evidence content to Gemini. Uses the same private-bucket,
    service-role-key access as upload_file."""
    settings = get_settings()
    url = f"{settings.supabase_url}/storage/v1/object/{bucket}/{path}"
    response = _client().get(url, headers=_headers(), timeout=30.0)
    if response.status_code != 200:
        raise EvidenceDownloadError(f"Storage download failed with status {response.status_code}.")
    return response.content


def create_signed_url(bucket: str, path: str, expires_in: int = 300) -> str:
    settings = get_settings()
    url = f"{settings.supabase_url}/storage/v1/object/sign/{bucket}/{path}"
    response = _client().post(url, json={"expiresIn": expires_in}, headers=_headers(), timeout=15.0)
    if response.status_code != 200:
        raise EvidenceUploadError(f"Could not create a signed URL (status {response.status_code}).")

    signed_path = response.json().get("signedURL")
    if not signed_path:
        raise EvidenceUploadError("Storage did not return a signed URL.")
    return f"{settings.supabase_url}/storage/v1{signed_path}"
