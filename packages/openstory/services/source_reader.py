from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path


class SourceReadError(ValueError):
    pass


class UnsupportedSourceTypeError(SourceReadError):
    pass


class SourceDecodeError(SourceReadError):
    pass


class EmptySourceError(SourceReadError):
    pass


MEDIA_TYPES = {
    ".md": "text/markdown",
    ".txt": "text/plain",
}


@dataclass(frozen=True, slots=True)
class ReadSourceResult:
    filename: str
    media_type: str
    text: str
    sha256: str


def read_source(filename: str, content: bytes) -> ReadSourceResult:
    safe_filename = Path(filename.replace("\\", "/")).name
    extension = Path(safe_filename).suffix.lower()
    try:
        media_type = MEDIA_TYPES[extension]
    except KeyError as error:
        raise UnsupportedSourceTypeError("Only .txt and .md source files are supported.") from error

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SourceDecodeError("Source files must be valid UTF-8.") from error
    if not text.strip():
        raise EmptySourceError("Source file cannot be empty.")

    return ReadSourceResult(
        filename=safe_filename,
        media_type=media_type,
        text=text,
        sha256=sha256(content).hexdigest(),
    )

