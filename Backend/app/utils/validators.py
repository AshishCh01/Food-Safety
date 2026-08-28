from app.core.config import get_settings
from app.utils.exceptions import FileTooLargeError, UnsupportedFileTypeError

ALLOWED_EVIDENCE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "video/mp4",
    "application/pdf",
}

MAX_EVIDENCE_FILE_SIZE_BYTES = 15 * 1024 * 1024

ALLOWED_RAG_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
}


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


def validate_rag_document_file(filename: str, content_type: str | None, size: int) -> None:
    if content_type not in ALLOWED_RAG_DOCUMENT_MIME_TYPES:
        raise UnsupportedFileTypeError(
            f"File type '{content_type or 'unknown'}' is not supported for knowledge base uploads."
        )
    if size <= 0:
        raise UnsupportedFileTypeError("Uploaded file is empty.")
    max_bytes = get_settings().rag_max_upload_size_mb * 1024 * 1024
    if size > max_bytes:
        raise FileTooLargeError(f"File exceeds the maximum allowed size of {get_settings().rag_max_upload_size_mb}MB.")
