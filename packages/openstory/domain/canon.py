from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EntityKind(StrEnum):
    CHARACTER = "character"
    LOCATION = "location"
    OBJECT = "object"
    FACTION = "faction"
    CREATURE = "creature"
    CONCEPT = "concept"


class CanonEntity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    kind: EntityKind
    canonical_name: str = Field(min_length=1, max_length=300)
    aliases: list[str] = Field(default_factory=list)
    summary: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("canonical_name")
    @classmethod
    def normalize_canonical_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("Canonical name cannot be empty.")
        return normalized


class CanonFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    subject_entity_id: str = Field(min_length=1)
    predicate: str = Field(min_length=1, max_length=300)
    object_entity_id: str | None = None
    value: Any | None = None
    valid_from_ordinal: int | None = None
    valid_to_ordinal: int | None = None
    source_chunk_id: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)

    @field_validator("predicate", "source_chunk_id", "evidence")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be blank.")
        return value

    @model_validator(mode="after")
    def requires_object_or_value(self) -> "CanonFact":
        if self.object_entity_id is None and self.value is None:
            raise ValueError("A canon fact requires an object entity or a value.")
        return self


class ExtractedEntity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ref: str = Field(min_length=1)
    kind: EntityKind
    canonical_name: str = Field(min_length=1, max_length=300)
    aliases: list[str] = Field(default_factory=list)
    summary: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("ref", "canonical_name")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be blank.")
        return value


class ExtractedFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    subject_ref: str = Field(min_length=1)
    predicate: str = Field(min_length=1, max_length=300)
    object_ref: str | None = None
    value: Any | None = None
    valid_from_ordinal: int | None = None
    valid_to_ordinal: int | None = None
    evidence: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)

    @field_validator("subject_ref", "predicate", "evidence")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be blank.")
        return value

    @model_validator(mode="after")
    def requires_object_or_value(self) -> "ExtractedFact":
        if self.object_ref is None and self.value is None:
            raise ValueError("An extracted fact requires an object reference or a value.")
        return self


class CanonExtractionResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    entities: list[ExtractedEntity] = Field(default_factory=list)
    facts: list[ExtractedFact] = Field(default_factory=list)
    unresolved_references: list[str] = Field(default_factory=list)


class CanonExtractionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: str
    source_chunk_ids: list[str]
    entities: list[CanonEntity]
    facts: list[CanonFact]
    unresolved_references: list[str]


class CanonSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: str
    ordinal: int
    entities: list[CanonEntity]
    facts: list[CanonFact]
