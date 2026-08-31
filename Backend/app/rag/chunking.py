"""Section-aware chunking (docs/RAG_ARCHITECTURE.md section 6). Prefers
splitting on detected headings over blind fixed-size chunking, so a chunk
carries a meaningful `section_title` where possible.

A chunk never spans pages - each page's text is split independently, so
`page_number` always stays exact and traceable back to the source PDF. This
is a deliberate simplification: a section that happens to straddle a page
break becomes two chunks instead of one, in exchange for citations that are
never ambiguous about which page they came from.
"""

import re
from dataclasses import dataclass

from app.core.config import get_settings
from app.rag.parsing import PageText

_MARKDOWN_HEADING_RE = re.compile(r"^#{1,6}\s+(.*\S)\s*$")
_NUMBERED_HEADING_RE = re.compile(r"^\s*\d+(?:\.\d+)*[.)]?\s+[A-Z][A-Za-z0-9 ,&/\-]{2,80}\s*$")
_ALLCAPS_HEADING_RE = re.compile(r"^[A-Z][A-Z0-9 ,&/\-]{3,79}$")


@dataclass
class Chunk:
    chunk_index: int
    content: str
    page_number: int | None
    section_title: str | None


def _detect_heading(line: str) -> str | None:
    stripped = line.strip()
    if not stripped:
        return None
    markdown_match = _MARKDOWN_HEADING_RE.match(stripped)
    if markdown_match:
        return markdown_match.group(1).strip()
    if _NUMBERED_HEADING_RE.match(stripped):
        return stripped
    if _ALLCAPS_HEADING_RE.match(stripped) and any(char.isalpha() for char in stripped):
        return stripped
    return None


def _split_into_sections(text: str) -> list[tuple[str | None, str]]:
    """Splits page text into (section_title, section_body) pairs. Text before
    the first detected heading has section_title=None."""
    sections: list[tuple[str | None, list[str]]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        heading = _detect_heading(line)
        if heading:
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = heading
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_title, current_lines))

    return [
        (title, "\n".join(lines).strip())
        for title, lines in sections
        if "\n".join(lines).strip()
    ]


def _split_by_size(text: str, target_chars: int, overlap_chars: int) -> list[str]:
    if len(text) <= target_chars:
        return [text]

    # A natural break (paragraph/sentence) is only accepted if it falls in
    # the back half of the window, close to `end` - never near `start`. Text
    # like a dense list of legal definitions can have long stretches with no
    # "\n\n" and only a stray ". " early in the window; without this floor,
    # rfind() would return that early match on every iteration (it's still
    # the rightmost one in [start, end)), `end` would stay pinned there, and
    # the overlap-based advance would collapse to `start + 1` - crawling one
    # character at a time and re-emitting nearly-identical overlapping
    # pieces until `start` finally passes that fixed point.
    min_boundary_search_start_ratio = 0.5

    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + target_chars, len(text))
        if end < len(text):
            search_start = start + int((end - start) * min_boundary_search_start_ratio)
            boundary = text.rfind("\n\n", search_start, end)
            if boundary <= start:
                boundary = text.rfind(". ", search_start, end)
            if boundary > start:
                end = boundary + 1
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap_chars, start + 1)
    return pieces


def _merge_small_sections(
    sections: list[tuple[str | None, str]], target_chars: int
) -> list[tuple[str | None, str]]:
    """Combines consecutive small sections (on the same page) up toward
    `target_chars` instead of emitting one chunk per detected heading
    regardless of size. A densely-numbered legal document can detect a
    heading every one or two sentences (e.g. "3. Definitions", "(1)..."),
    which without merging produces hundreds of near-empty chunks - hurting
    both ingestion cost (one embedding call each) and retrieval quality (a
    chunk too short to carry context on its own). A section already at or
    over `target_chars` is left alone so `_split_by_size` still handles it."""
    merged: list[tuple[str | None, str]] = []
    buffer_title: str | None = None
    buffer_parts: list[str] = []
    buffer_len = 0

    def flush() -> None:
        nonlocal buffer_title, buffer_parts, buffer_len
        if buffer_parts:
            merged.append((buffer_title, "\n\n".join(buffer_parts)))
        buffer_title, buffer_parts, buffer_len = None, [], 0

    for section_title, body in sections:
        if len(body) >= target_chars:
            flush()
            merged.append((section_title, body))
            continue

        if buffer_parts and buffer_len + len(body) > target_chars:
            flush()

        if buffer_title is None:
            buffer_title = section_title
        buffer_parts.append(body)
        buffer_len += len(body)

    flush()
    return merged


def chunk_pages(pages: list[PageText]) -> list[Chunk]:
    settings = get_settings()
    chunks: list[Chunk] = []
    index = 0

    for page in pages:
        if not page.text.strip():
            continue
        sections = _merge_small_sections(_split_into_sections(page.text), settings.rag_chunk_target_chars)
        for section_title, body in sections:
            for piece in _split_by_size(body, settings.rag_chunk_target_chars, settings.rag_chunk_overlap_chars):
                chunks.append(
                    Chunk(
                        chunk_index=index,
                        content=piece,
                        page_number=page.page_number,
                        section_title=section_title,
                    )
                )
                index += 1

    return chunks
