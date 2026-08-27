"""Thin wrapper around the Supabase Storage REST API.

Uses the service-role key so uploads/signed URLs work against private
buckets; this key must never be shipped to the frontend. All network calls
are isolated behind `upload_file`/`create_signed_url` so callers (and tests)
can monkeypatch them without hitting the network.
"""

import httpx

from app.core.config import get_settings
from app.utils.exceptions import EvidenceUploadError


def _headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
    }


def upload_file(bucket: str, path: str, content: bytes, content_type: str) -> str:
    settings = get_settings()
    url = f"{settings.supabase_url}/storage/v1/object/{bucket}/{path}"
    response = httpx.post(
        url,
        content=content,
        headers={**_headers(), "Content-Type": content_type},
        timeout=30.0,
    )
    if response.status_code not in (200, 201):
        raise EvidenceUploadError(f"Storage upload failed with status {response.status_code}.")
    return path


def create_signed_url(bucket: str, path: str, expires_in: int = 300) -> str:
    settings = get_settings()
    url = f"{settings.supabase_url}/storage/v1/object/sign/{bucket}/{path}"
    response = httpx.post(url, json={"expiresIn": expires_in}, headers=_headers(), timeout=15.0)
    if response.status_code != 200:
        raise EvidenceUploadError(f"Could not create a signed URL (status {response.status_code}).")

    signed_path = response.json().get("signedURL")
    if not signed_path:
        raise EvidenceUploadError("Storage did not return a signed URL.")
    return f"{settings.supabase_url}/storage/v1{signed_path}"
