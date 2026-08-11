import pytest


def test_source_reader_sanitizes_filename_and_hashes_original_bytes() -> None:
    from openstory.services.source_reader import read_source

    result = read_source("../../story.md", b"hello")

    assert result.filename == "story.md"
    assert result.media_type == "text/markdown"
    assert result.text == "hello"
    assert result.sha256 == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


def test_source_reader_rejects_unsupported_extension() -> None:
    from openstory.services.source_reader import UnsupportedSourceTypeError, read_source

    with pytest.raises(UnsupportedSourceTypeError):
        read_source("story.pdf", b"not a supported source")


def test_source_reader_rejects_invalid_utf8() -> None:
    from openstory.services.source_reader import SourceDecodeError, read_source

    with pytest.raises(SourceDecodeError):
        read_source("story.txt", b"\xff")


def test_source_reader_rejects_empty_text() -> None:
    from openstory.services.source_reader import EmptySourceError, read_source

    with pytest.raises(EmptySourceError):
        read_source("story.txt", b"  \n")

