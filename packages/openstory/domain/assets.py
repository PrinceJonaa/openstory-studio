from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from openstory.domain.project import utc_now
from openstory.domain.status import ProductionStatus


class ImageGenerationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    output_path: Path
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    seed: int | None = None
    provider: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RenderVersion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    panel_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    output_path: str = Field(min_length=1)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    seed: int | None = None
    provider: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: ProductionStatus = ProductionStatus.DRAFT
    created_at: datetime = Field(default_factory=utc_now)
