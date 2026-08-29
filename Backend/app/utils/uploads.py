from fastapi import UploadFile

from app.utils.exceptions import FileTooLargeError

_CHUNK_SIZE = 1024 * 1024  # 1MB


async def read_upload_bounded(file: UploadFile, max_bytes: int) -> bytes:
    """Reads an UploadFile in chunks, aborting as soon as `max_bytes` is
    exceeded instead of buffering an arbitrarily large body into memory
    before the size check runs (see docs/SECURITY_AND_RBAC.md section 8,
    "validate file type and size") - a naive `await file.read()` followed by
    a length check has no bound on how much memory a single request can
    consume while it's read."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise FileTooLargeError(f"File exceeds the maximum allowed size of {max_bytes // (1024 * 1024)}MB.")
        chunks.append(chunk)
    return b"".join(chunks)
