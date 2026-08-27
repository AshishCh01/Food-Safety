from app.utils.exceptions import FileTooLargeError, UnsupportedFileTypeError

ALLOWED_EVIDENCE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "video/mp4",
    "application/pdf",
}

MAX_EVIDENCE_FILE_SIZE_BYTES = 15 * 1024 * 1024


def validate_evidence_file(filename: str, content_type: str | None, size: int) -> None:
    if content_type not in ALLOWED_EVIDENCE_MIME_TYPES:
        raise UnsupportedFileTypeError(
            f"File type '{content_type or 'unknown'}' is not supported for evidence uploads."
        )
    if size <= 0:
        raise UnsupportedFileTypeError("Uploaded file is empty.")
    if size > MAX_EVIDENCE_FILE_SIZE_BYTES:
        raise FileTooLargeError(
            f"File exceeds the maximum allowed size of {MAX_EVIDENCE_FILE_SIZE_BYTES // (1024 * 1024)}MB."
        )
