import pytest

from app.utils.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.utils.validators import MAX_EVIDENCE_FILE_SIZE_BYTES, validate_evidence_file


def test_accepts_supported_image_type() -> None:
    validate_evidence_file("photo.jpg", "image/jpeg", 1024)


def test_rejects_unsupported_content_type() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        validate_evidence_file("notes.txt", "text/plain", 1024)


def test_rejects_missing_content_type() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        validate_evidence_file("mystery", None, 1024)


def test_rejects_empty_file() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        validate_evidence_file("photo.jpg", "image/jpeg", 0)


def test_rejects_oversized_file() -> None:
    with pytest.raises(FileTooLargeError):
        validate_evidence_file("video.mp4", "video/mp4", MAX_EVIDENCE_FILE_SIZE_BYTES + 1)


def test_accepts_file_at_exact_size_limit() -> None:
    validate_evidence_file("video.mp4", "video/mp4", MAX_EVIDENCE_FILE_SIZE_BYTES)
