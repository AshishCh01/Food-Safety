"""Document loading/parsing for the RAG ingestion pipeline
(docs/RAG_ARCHITECTURE.md section 4). Supports PDF and plain text/markdown
documents - the only formats the knowledge base accepts (see
app/utils/validators.py:validate_rag_document_file).
"""

import io
from dataclasses import dataclass

import pypdf

from app.utils.exceptions import RagIngestionError, UnsupportedFileTypeError

SUPPORTED_MIME_TYPES = {"application/pdf", "text/plain", "text/markdown"}


@dataclass
class PageText:
    """One page of extracted text. `page_number` is 1-indexed and only set for
    paginated formats (PDF); plain text/markdown documents have no natural page
    boundary, so `page_number` is None there."""

    page_number: int | None
    text: str


def parse_pdf(file_bytes: bytes) -> list[PageText]:
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        return [PageText(page_number=index, text=page.extract_text() or "") for index, page in enumerate(reader.pages, start=1)]
    except Exception as exc:
        raise RagIngestionError(f"Could not parse the PDF file: {exc}") from exc


def parse_text(file_bytes: bytes) -> list[PageText]:
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RagIngestionError("Could not decode the text file as UTF-8.") from exc
    return [PageText(page_number=None, text=text)]


def load_document(file_bytes: bytes, mime_type: str) -> list[PageText]:
    if mime_type == "application/pdf":
        return parse_pdf(file_bytes)
    if mime_type in ("text/plain", "text/markdown"):
        return parse_text(file_bytes)
    raise UnsupportedFileTypeError(f"File type '{mime_type}' is not supported for RAG ingestion.")
