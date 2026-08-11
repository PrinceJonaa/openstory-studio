from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from openstory.domain.project import utc_now


class JobKind(StrEnum):
    CANON_EXTRACT = "canon_extract"
    EPISODE_ADAPT = "episode_adapt"
    STORYBOARD_BUILD = "storyboard_build"
    IMAGE_RENDER = "image_render"
    EXPORT = "export"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Job(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    project_id: str
    kind: JobKind
    status: JobStatus = JobStatus.QUEUED
    progress_current: int = Field(default=0, ge=0)
    progress_total: int | None = Field(default=None, ge=0)
    error: str | None = Field(default=None, max_length=4_000)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def progress_does_not_exceed_total(self) -> "Job":
        if (
            self.progress_total is not None
            and self.progress_current > self.progress_total
        ):
            raise ValueError("Job progress cannot exceed progress_total.")
        return self


class JobRunResult[T](BaseModel):
    model_config = ConfigDict(frozen=True)

    job: Job
    result: T
