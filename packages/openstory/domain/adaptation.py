from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from openstory.domain.project import TargetFormat
from openstory.domain.status import ProductionStatus


class AdaptEpisodeCommand(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: str = Field(min_length=1)
    source_chunk_ids: list[str] = Field(min_length=1)
    number: int = Field(ge=1)
    target_format: TargetFormat

    @field_validator("source_chunk_ids")
    @classmethod
    def source_chunks_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("Source chunk IDs must be unique.")
        if any(not chunk_id.strip() for chunk_id in value):
            raise ValueError("Source chunk IDs cannot be blank.")
        return value


class EpisodeDraft(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str = Field(min_length=1, max_length=300)
    logline: str = Field(min_length=1, max_length=2_000)
    adaptation_notes: str = Field(min_length=1, max_length=10_000)


class SceneDraft(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ordinal: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=300)
    purpose: str = Field(min_length=1, max_length=2_000)
    location_ref: str | None = None
    character_refs: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1, max_length=10_000)


class EpisodeAdaptationResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    episode: EpisodeDraft
    scenes: list[SceneDraft] = Field(min_length=1)

    @model_validator(mode="after")
    def scene_ordinals_are_contiguous(self) -> "EpisodeAdaptationResponse":
        ordinals = [scene.ordinal for scene in self.scenes]
        if ordinals != list(range(1, len(self.scenes) + 1)):
            raise ValueError("Scene ordinals must be unique and contiguous from 1.")
        return self


class Episode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    number: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=300)
    source_chunk_ids: list[str] = Field(min_length=1)
    logline: str = Field(min_length=1, max_length=2_000)
    adaptation_notes: str = Field(min_length=1, max_length=10_000)
    status: ProductionStatus = ProductionStatus.DRAFT


class Scene(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    episode_id: str = Field(min_length=1)
    ordinal: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=300)
    purpose: str = Field(min_length=1, max_length=2_000)
    location_entity_id: str | None = None
    character_entity_ids: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1, max_length=10_000)
    status: ProductionStatus = ProductionStatus.DRAFT


class EpisodeDetail(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    episode: Episode
    scenes: list[Scene]
