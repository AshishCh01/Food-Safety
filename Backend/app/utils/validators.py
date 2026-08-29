import re

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

# Extensions accepted per declared content-type. A mismatch (e.g. a
# `.html` file declared as `image/jpeg`) is rejected even if the MIME type
# itself is on the allowlist above - see docs/SECURITY_AND_RBAC.md section 8
# ("prevent path traversal", "validate file type").
_EVIDENCE_EXTENSIONS: dict[str, set[str]] = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
    "video/mp4": {".mp4"},
    "application/pdf": {".pdf"},
}

_RAG_DOCUMENT_EXTENSIONS: dict[str, set[str]] = {
    "application/pdf": {".pdf"},
    "text/plain": {".txt"},
    "text/markdown": {".md", ".markdown"},
}

# Only characters safe in a storage object key / URL path segment survive;
# everything else (path separators, "..", control characters, unicode
# homoglyphs, etc.) is collapsed to "_". This runs before the sanitized name
# is ever used to build a storage path (app/services/evidence_service.py,
# app/services/rag_document_service.py) or interpolated into a Supabase
# Storage REST URL (app/services/storage_service.py) - neither of those
# URL-encodes the path segment, so an unsanitized filename containing "/",
# "..", or "?" could otherwise redirect the write to an unintended object key.
_UNSAFE_FILENAME_CHARS_RE = re.compile(r"[^A-Za-z0-9._-]+")
_MAX_FILENAME_LENGTH = 150


def sanitize_filename(filename: str | None, *, default: str = "file") -> str:
    name = (filename or "").strip()
    # Strip any directory component a client might send (path traversal
    # guard) regardless of which slash style it used.
    name = name.replace("\\", "/").rsplit("/", 1)[-1]
    name = _UNSAFE_FILENAME_CHARS_RE.sub("_", name)
    name = name.lstrip(".-")  # no leading dots/dashes (hidden files, "-rf" style args)
    name = name[:_MAX_FILENAME_LENGTH]
    return name or default


def _extension_of(filename: str) -> str:
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


def _matches_signature(content_type: str, header: bytes) -> bool:
    """Sniffs the first bytes of the file against the magic number expected
    for `content_type`, so a client can't bypass validation by declaring an
    arbitrary `Content-Type` header (fully attacker-controlled) for a file
    whose actual content is something else entirely (e.g. HTML/SVG with an
    embedded script, disguised as `image/jpeg`)."""
    if content_type == "image/jpeg":
        return header.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/webp":
        return header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    if content_type == "video/mp4":
        # ISO base media file format: a 4-byte box size followed by an
        # "ftyp" box type, normally at offset 4. A handful of major brands
        # exist (isom, mp42, MSNV, ...); we only need to confirm it's an
        # MP4/QuickTime-family container, not which brand.
        return header[4:8] == b"ftyp"
    if content_type == "application/pdf":
        return header.startswith(b"%PDF-")
    if content_type == "text/plain" or content_type == "text/markdown":
        # No fixed magic number for plain text. Reject content containing
        # NUL bytes (a strong signal of disguised binary content) and
        # require the sampled header to decode as UTF-8 text.
        if b"\x00" in header:
            return False
        try:
            header.decode("utf-8")
        except UnicodeDecodeError:
            return False
        return True
    return False


def _validate_file(
    *,
    filename: str | None,
    content_type: str | None,
    size: int,
    header: bytes,
    allowed_mime_types: set[str],
    allowed_extensions: dict[str, set[str]],
    max_bytes: int,
    default_filename: str,
) -> str:
    if content_type not in allowed_mime_types:
        raise UnsupportedFileTypeError(f"File type '{content_type or 'unknown'}' is not supported.")
    if size <= 0:
        raise UnsupportedFileTypeError("Uploaded file is empty.")
    if size > max_bytes:
        raise FileTooLargeError(f"File exceeds the maximum allowed size of {max_bytes // (1024 * 1024)}MB.")

    sanitized = sanitize_filename(filename, default=default_filename)
    extension = _extension_of(sanitized)
    if extension not in allowed_extensions.get(content_type, set()):
        raise UnsupportedFileTypeError(
            f"File extension '{extension or '(none)'}' does not match the declared file type '{content_type}'."
        )

    if not _matches_signature(content_type, header):
        raise UnsupportedFileTypeError("File content does not match its declared file type.")

    return sanitized


def validate_evidence_file(filename: str | None, content_type: str | None, size: int, header: bytes) -> str:
    """Validates an evidence upload and returns a sanitized filename safe to
    use in a storage key. Raises UnsupportedFileTypeError/FileTooLargeError."""
    return _validate_file(
        filename=filename,
        content_type=content_type,
        size=size,
        header=header,
        allowed_mime_types=ALLOWED_EVIDENCE_MIME_TYPES,
        allowed_extensions=_EVIDENCE_EXTENSIONS,
        max_bytes=MAX_EVIDENCE_FILE_SIZE_BYTES,
        default_filename="upload",
    )


def validate_rag_document_file(filename: str | None, content_type: str | None, size: int, header: bytes) -> str:
    """Validates a knowledge-base document upload and returns a sanitized
    filename safe to use in a storage key."""
    max_bytes = get_settings().rag_max_upload_size_mb * 1024 * 1024
    return _validate_file(
        filename=filename,
        content_type=content_type,
        size=size,
        header=header,
        allowed_mime_types=ALLOWED_RAG_DOCUMENT_MIME_TYPES,
        allowed_extensions=_RAG_DOCUMENT_EXTENSIONS,
        max_bytes=max_bytes,
        default_filename="document",
    )
