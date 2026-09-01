import json

import pytest

from app.rag import parsing
from app.utils.exceptions import (
    GeminiRateLimitedError,
    GeminiRequestError,
    GeminiUnavailableError,
    RagIngestionError,
    UnsupportedFileTypeError,
)


class _FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakeReader:
    def __init__(self, _stream) -> None:
        self.pages = [_FakePage("Page one content."), _FakePage("Page two content.")]


def test_parse_pdf_returns_one_entry_per_page(monkeypatch) -> None:
    monkeypatch.setattr(parsing.pypdf, "PdfReader", _FakeReader)

    pages = parsing.parse_pdf(b"fake-pdf-bytes")

    assert [p.page_number for p in pages] == [1, 2]
    assert pages[0].text == "Page one content."
    assert pages[1].text == "Page two content."


def test_parse_pdf_wraps_reader_failure(monkeypatch) -> None:
    def _raise(_stream):
        raise ValueError("corrupt pdf")

    monkeypatch.setattr(parsing.pypdf, "PdfReader", _raise)

    with pytest.raises(RagIngestionError):
        parsing.parse_pdf(b"not a pdf")


def test_parse_text_returns_single_page_with_no_page_number() -> None:
    pages = parsing.parse_text("Hello regulations.".encode("utf-8"))

    assert len(pages) == 1
    assert pages[0].page_number is None
    assert pages[0].text == "Hello regulations."


def test_parse_text_rejects_invalid_utf8() -> None:
    with pytest.raises(RagIngestionError):
        parsing.parse_text(b"\xff\xfe\x00\x00invalid")


def test_load_document_dispatches_pdf(monkeypatch) -> None:
    monkeypatch.setattr(parsing.pypdf, "PdfReader", _FakeReader)

    pages = parsing.load_document(b"fake", "application/pdf")

    assert len(pages) == 2


def test_load_document_dispatches_text() -> None:
    pages = parsing.load_document(b"hello", "text/plain")

    assert pages[0].text == "hello"


def test_load_document_rejects_unsupported_mime_type() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        parsing.load_document(b"data", "video/mp4")


class _FakeEmptyTextPage(_FakePage):
    def __init__(self) -> None:
        super().__init__("")


class _FakeAllBlankReader:
    """Simulates a PDF where every page has no extractable text layer, so
    every page falls onto the OCR path in `parse_pdf`."""

    def __init__(self, _stream, *, page_count: int) -> None:
        self.pages = [_FakeEmptyTextPage() for _ in range(page_count)]


def test_ocr_page_image_retries_on_rate_limit_then_succeeds(monkeypatch) -> None:
    calls = {"count": 0}

    def _flaky_call(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise GeminiRateLimitedError()
        return json.dumps({"text": "recovered on retry"})

    monkeypatch.setattr(parsing.ai_service, "generate_structured_json_with_media", _flaky_call)

    result = parsing._ocr_page_image(b"fake-image-bytes")

    assert result == "recovered on retry"
    assert calls["count"] == 2


def test_ocr_page_image_gives_up_after_persistent_transient_failure(monkeypatch, caplog) -> None:
    def _always_unavailable(*_args, **_kwargs):
        raise GeminiUnavailableError()

    monkeypatch.setattr(parsing.ai_service, "generate_structured_json_with_media", _always_unavailable)

    with caplog.at_level("WARNING"):
        result = parsing._ocr_page_image(b"fake-image-bytes")

    assert result == ""
    assert any("OCR transcription failed" in record.message for record in caplog.records)


def test_ocr_page_image_does_not_retry_non_retryable_request_error(monkeypatch) -> None:
    calls = {"count": 0}

    def _reject(*_args, **_kwargs):
        calls["count"] += 1
        raise GeminiRequestError()

    monkeypatch.setattr(parsing.ai_service, "generate_structured_json_with_media", _reject)

    with pytest.raises(GeminiRequestError):
        parsing._ocr_page_image(b"fake-image-bytes")

    assert calls["count"] == 1


def test_parse_pdf_raises_when_ocr_page_count_exceeds_cap(monkeypatch) -> None:
    too_many_pages = parsing._MAX_OCR_PAGES_PER_DOCUMENT + 1

    def _fake_reader(stream):
        return _FakeAllBlankReader(stream, page_count=too_many_pages)

    monkeypatch.setattr(parsing.pypdf, "PdfReader", _fake_reader)

    def _fail_if_called(*_args, **_kwargs):
        raise AssertionError("OCR should not be invoked once the page-count cap is exceeded")

    monkeypatch.setattr(parsing, "_ocr_pdf_page", _fail_if_called)

    with pytest.raises(RagIngestionError):
        parsing.parse_pdf(b"fake-pdf-bytes")
