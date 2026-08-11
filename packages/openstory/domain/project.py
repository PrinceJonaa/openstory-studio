import re
import unicodedata
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TargetFormat(StrEnum):
    STORYBOARD = "storyboard"
    COMIC = "comic"
    WEBTOON = "webtoon"
    ANIME = "anime"
    FILM = "film"


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_project_name(value: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError("Project name cannot be empty.")
    return normalized


def slugify(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    if not slug:
        raise ValueError("Project name must contain a letter or number.")
    return slug


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2_000)
    target_format: TargetFormat

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return normalize_project_name(value)


class Project(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: str
    name: str
    slug: str
    description: str | None = None
    target_format: TargetFormat
    created_at: datetime
    updated_at: datetime

