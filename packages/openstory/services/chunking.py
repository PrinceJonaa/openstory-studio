import re
from dataclasses import dataclass

MARKDOWN_HEADING = re.compile(r"^#{1,6}[ \t]+(.+?)\s*$")
CHAPTER_PATTERN = re.compile(
    r"^(?:chapter|part)\s+(?:\d+|[ivxlcdm]+)(?:\s*[:.-]\s*.+)?$",
    re.IGNORECASE,
)
PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n")


@dataclass(frozen=True, slots=True)
class ChunkDraft:
    heading: str | None
    text: str
    start_offset: int
    end_offset: int


def _heading_markers(text: str, media_type: str) -> list[tuple[int, str]]:
    markers: list[tuple[int, str]] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        candidate = line.rstrip("\r\n")
        if media_type == "text/markdown":
            match = MARKDOWN_HEADING.fullmatch(candidate)
            if match is not None:
                markers.append((offset, match.group(1).strip()))
        elif CHAPTER_PATTERN.fullmatch(candidate.strip()):
            markers.append((offset, candidate.strip()))
        offset += len(line)
    return markers


def _paragraph_spans(text: str, start: int, end: int) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    cursor = start
    for match in PARAGRAPH_BREAK.finditer(text, start, end):
        spans.append((cursor, match.end()))
        cursor = match.end()
    if cursor < end:
        spans.append((cursor, end))
    return spans or [(start, end)]


def _bounded_spans(text: str, start: int, end: int, max_chars: int) -> list[tuple[int, int]]:
    chunks: list[tuple[int, int]] = []
    current_start: int | None = None
    current_end: int | None = None

    def flush() -> None:
        nonlocal current_start, current_end
        if current_start is not None and current_end is not None:
            chunks.append((current_start, current_end))
        current_start = None
        current_end = None

    for paragraph_start, paragraph_end in _paragraph_spans(text, start, end):
        paragraph_length = paragraph_end - paragraph_start
        if paragraph_length > max_chars:
            flush()
            split_start = paragraph_start
            while split_start < paragraph_end:
                split_end = min(split_start + max_chars, paragraph_end)
                chunks.append((split_start, split_end))
                split_start = split_end
            continue

        if current_start is None:
            current_start = paragraph_start
            current_end = paragraph_end
            continue

        if paragraph_end - current_start <= max_chars:
            current_end = paragraph_end
        else:
            flush()
            current_start = paragraph_start
            current_end = paragraph_end

    flush()
    return chunks


def chunk_source(
    text: str,
    media_type: str,
    *,
    max_chars: int = 4_000,
) -> list[ChunkDraft]:
    if not text:
        raise ValueError("Source text cannot be empty.")
    if max_chars < 1:
        raise ValueError("max_chars must be positive.")

    markers = _heading_markers(text, media_type)
    sections: list[tuple[int, int, str | None]]
    if markers:
        sections = []
        for index, (start, marker_heading) in enumerate(markers):
            if index == 0 and start > 0 and not text[:start].strip():
                start = 0
            end = markers[index + 1][0] if index + 1 < len(markers) else len(text)
            sections.append((start, end, marker_heading))
        first_start = markers[0][0]
        if first_start > 0 and text[:first_start].strip():
            sections.insert(0, (0, first_start, None))
    else:
        sections = [(0, len(text), None)]

    drafts: list[ChunkDraft] = []
    for section_start, section_end, heading in sections:
        for start, end in _bounded_spans(text, section_start, section_end, max_chars):
            drafts.append(
                ChunkDraft(
                    heading=heading,
                    text=text[start:end],
                    start_offset=start,
                    end_offset=end,
                )
            )
    return drafts
