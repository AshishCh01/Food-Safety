import pytest

from app.utils.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.utils.validators import (
    MAX_EVIDENCE_FILE_SIZE_BYTES,
    sanitize_filename,
    validate_evidence_file,
    validate_rag_document_file,
)

JPEG_HEADER = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00"
PNG_HEADER = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
WEBP_HEADER = b"RIFF\x24\x00\x00\x00WEBPVP8 "
MP4_HEADER = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00"
PDF_HEADER = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3"
TEXT_HEADER = b"This is a plain text knowledge base document."


def test_accepts_supported_image_type() -> None:
    filename = validate_evidence_file("photo.jpg", "image/jpeg", 1024, JPEG_HEADER)
    assert filename == "photo.jpg"


def test_rejects_unsupported_content_type() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        validate_evidence_file("notes.txt", "text/plain", 1024, TEXT_HEADER)


def test_rejects_missing_content_type() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        validate_evidence_file("mystery", None, 1024, b"")


def test_rejects_empty_file() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        validate_evidence_file("photo.jpg", "image/jpeg", 0, JPEG_HEADER)


def test_rejects_oversized_file() -> None:
    with pytest.raises(FileTooLargeError):
        validate_evidence_file("video.mp4", "video/mp4", MAX_EVIDENCE_FILE_SIZE_BYTES + 1, MP4_HEADER)


def test_accepts_file_at_exact_size_limit() -> None:
    validate_evidence_file("video.mp4", "video/mp4", MAX_EVIDENCE_FILE_SIZE_BYTES, MP4_HEADER)


def test_accepts_all_supported_evidence_signatures() -> None:
    assert validate_evidence_file("photo.png", "image/png", 1024, PNG_HEADER) == "photo.png"
    assert validate_evidence_file("photo.webp", "image/webp", 1024, WEBP_HEADER) == "photo.webp"
    assert validate_evidence_file("receipt.pdf", "application/pdf", 1024, PDF_HEADER) == "receipt.pdf"


def test_rejects_content_that_does_not_match_declared_type() -> None:
    # Declares image/jpeg but the bytes are actually an HTML document - a
    # spoofed Content-Type header should not be trusted on its own.
    html_payload = b"<html><body><script>alert(1)</script></body></html>"
    with pytest.raises(UnsupportedFileTypeError):
        validate_evidence_file("photo.jpg", "image/jpeg", len(html_payload), html_payload[:16])


def test_rejects_extension_mismatched_with_declared_type() -> None:
    # Real JPEG bytes, but the filename claims a different (dangerous)
    # extension than what image/jpeg allows.
    with pytest.raises(UnsupportedFileTypeError):
        validate_evidence_file("payload.html", "image/jpeg", 1024, JPEG_HEADER)


def test_sanitizes_path_traversal_in_filename() -> None:
    filename = validate_evidence_file("../../etc/passwd.jpg", "image/jpeg", 1024, JPEG_HEADER)
    assert filename == "passwd.jpg"
    assert "/" not in filename
    assert ".." not in filename


def test_sanitizes_unsafe_characters_in_filename() -> None:
    filename = validate_evidence_file("weird name?.jpg", "image/jpeg", 1024, JPEG_HEADER)
    assert filename == "weird_name_.jpg"


def test_sanitize_filename_falls_back_to_default_when_empty() -> None:
    assert sanitize_filename("", default="upload") == "upload"
    assert sanitize_filename(None, default="upload") == "upload"
    assert sanitize_filename("///", default="upload") == "upload"


def test_validate_rag_document_accepts_pdf_and_text() -> None:
    assert validate_rag_document_file("law.pdf", "application/pdf", 1024, PDF_HEADER) == "law.pdf"
    assert validate_rag_document_file("sop.txt", "text/plain", 1024, TEXT_HEADER) == "sop.txt"


def test_validate_rag_document_rejects_binary_disguised_as_text() -> None:
    binary_payload = bytes(range(0, 16))  # contains NUL bytes, not valid UTF-8 text
    with pytest.raises(UnsupportedFileTypeError):
        validate_rag_document_file("notes.txt", "text/plain", len(binary_payload), binary_payload)
