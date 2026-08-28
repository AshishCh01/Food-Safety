import pytest

from app.rag import parsing
from app.utils.exceptions import RagIngestionError, UnsupportedFileTypeError


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
