from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SourceDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    project_id: str
    filename: str
    media_type: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    workspace_path: str

    @field_validator("filename")
    @classmethod
    def filename_is_a_basename(cls, value: str) -> str:
        if Path(value).name != value:
            raise ValueError("Source filename must be a basename.")
        return value


class SourceChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    document_id: str
    ordinal: int = Field(ge=1)
    heading: str | None = None
    text: str = Field(min_length=1)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)

    @model_validator(mode="after")
    def offsets_match_text(self) -> "SourceChunk":
        if self.end_offset <= self.start_offset:
            raise ValueError("end_offset must be greater than start_offset.")
        if self.end_offset - self.start_offset != len(self.text):
            raise ValueError("Chunk offsets must span exactly the chunk text.")
        return self


class SourceIngestionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    document: SourceDocument
    chunks: list[SourceChunk]

