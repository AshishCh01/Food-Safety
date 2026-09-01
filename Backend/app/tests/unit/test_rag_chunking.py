from app.rag import chunking
from app.rag.parsing import PageText


def test_markdown_heading_starts_new_chunk() -> None:
    page = PageText(page_number=1, text="# Personal Hygiene\n\nHands must be washed before handling food.")

    chunks = chunking.chunk_pages([page])

    assert len(chunks) == 1
    assert chunks[0].section_title == "Personal Hygiene"
    assert chunks[0].page_number == 1
    assert "washed" in chunks[0].content


def test_numbered_heading_is_detected() -> None:
    page = PageText(page_number=2, text="1.2 Storage Requirements\n\nPerishable food must be kept below 5C.")

    chunks = chunking.chunk_pages([page])

    assert chunks[0].section_title == "1.2 Storage Requirements"
    assert chunks[0].page_number == 2


def test_allcaps_heading_is_detected() -> None:
    page = PageText(page_number=1, text="FOOD SAMPLING PROCEDURE\n\nCollect at least three samples per batch.")

    chunks = chunking.chunk_pages([page])

    assert chunks[0].section_title == "FOOD SAMPLING PROCEDURE"


def test_text_before_first_heading_has_no_section_title() -> None:
    page = PageText(page_number=1, text="Introductory remarks with no heading yet.\n\n# Scope\n\nApplies statewide.")

    chunks = chunking.chunk_pages([page])

    assert chunks[0].section_title is None
    assert "Introductory remarks" in chunks[0].content
    assert chunks[1].section_title == "Scope"


def test_chunk_never_spans_pages() -> None:
    pages = [
        PageText(page_number=1, text="# Section A\n\nContent on page one."),
        PageText(page_number=2, text="More content, still logically part of section A, but on page two."),
    ]

    chunks = chunking.chunk_pages(pages)

    page_numbers = {chunk.page_number for chunk in chunks}
    assert page_numbers == {1, 2}
    assert all(chunk.page_number in (1, 2) for chunk in chunks)


def test_large_section_is_split_by_target_size(monkeypatch) -> None:
    monkeypatch.setattr(chunking, "get_settings", lambda: _FakeSettings(target_chars=50, overlap_chars=10))
    long_text = "This is a sentence about food safety regulations. " * 5
    page = PageText(page_number=1, text=long_text)

    chunks = chunking.chunk_pages([page])

    assert len(chunks) > 1
    assert all(len(chunk.content) <= 60 for chunk in chunks)


def test_blank_pages_produce_no_chunks() -> None:
    chunks = chunking.chunk_pages([PageText(page_number=1, text="   \n  \n"), PageText(page_number=2, text="")])

    assert chunks == []


def test_chunk_index_is_sequential_across_pages() -> None:
    pages = [
        PageText(page_number=1, text="# A\n\nfirst"),
        PageText(page_number=2, text="# B\n\nsecond"),
    ]

    chunks = chunking.chunk_pages(pages)

    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


class _FakeSettings:
    def __init__(self, target_chars: int, overlap_chars: int) -> None:
        self.rag_chunk_target_chars = target_chars
        self.rag_chunk_overlap_chars = overlap_chars
