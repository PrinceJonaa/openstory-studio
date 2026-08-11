from pathlib import Path


def test_markdown_ingestion_splits_headings() -> None:
    from openstory.services.chunking import chunk_source

    text = Path("tests/fixtures/glass_orchard.md").read_text()
    drafts = chunk_source(text, "text/markdown")

    assert [draft.heading for draft in drafts] == [
        "Chapter 1: The Shard",
        "Chapter 2: The Crossing",
    ]
    assert all(text[draft.start_offset : draft.end_offset] == draft.text for draft in drafts)


def test_plaintext_ingestion_detects_chapters() -> None:
    from openstory.services.chunking import chunk_source

    text = Path("tests/fixtures/glass_orchard.txt").read_text()
    drafts = chunk_source(text, "text/plain")

    assert len(drafts) == 2
    assert drafts[0].heading == "Chapter 1"
    assert drafts[1].heading == "CHAPTER II"
    assert all(text[draft.start_offset : draft.end_offset] == draft.text for draft in drafts)


def test_headingless_text_chunks_only_at_paragraph_boundaries() -> None:
    from openstory.services.chunking import chunk_source

    text = "First paragraph has words.\n\nSecond paragraph has more words.\n\nThird."
    drafts = chunk_source(text, "text/plain", max_chars=40)

    assert [draft.text for draft in drafts] == [
        "First paragraph has words.\n\n",
        "Second paragraph has more words.\n\nThird.",
    ]
    assert [draft.start_offset for draft in drafts] == [0, 28]
    assert [draft.end_offset for draft in drafts] == [28, len(text)]


def test_single_oversized_paragraph_is_split_without_losing_text() -> None:
    from openstory.services.chunking import chunk_source

    text = "abcdefghij"
    drafts = chunk_source(text, "text/plain", max_chars=4)

    assert [draft.text for draft in drafts] == ["abcd", "efgh", "ij"]
    assert "".join(draft.text for draft in drafts) == text
