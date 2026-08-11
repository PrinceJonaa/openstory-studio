from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from openstory.domain.status import ProductionStatus


class RenderStatus(StrEnum):
    UNRENDERED = "unrendered"
    QUEUED = "queued"
    RENDERED = "rendered"
    FAILED = "failed"


class DialogueLineDraft(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    speaker_ref: str | None = None
    speaker_name: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1, max_length=2_000)


class DialogueLine(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    speaker_entity_id: str | None = None
    speaker_name: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1, max_length=2_000)


class PanelDraft(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ordinal: int = Field(ge=1)
    shot_type: str = Field(min_length=1, max_length=200)
    framing: str = Field(min_length=1, max_length=500)
    action: str = Field(min_length=1, max_length=5_000)
    visual_description: str = Field(min_length=1, max_length=10_000)
    dialogue: list[DialogueLineDraft] = Field(default_factory=list)
    character_refs: list[str] = Field(default_factory=list)
    location_ref: str | None = None
    image_prompt: str = Field(min_length=1, max_length=10_000)
    negative_prompt: str | None = Field(default=None, max_length=5_000)

    @field_validator(
        "shot_type",
        "framing",
        "action",
        "visual_description",
        "image_prompt",
    )
    @classmethod
    def production_fields_are_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Storyboard production fields cannot be blank.")
        return value


class StoryboardBuildResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    panels: list[PanelDraft] = Field(min_length=1, max_length=24)

    @model_validator(mode="after")
    def panel_ordinals_are_contiguous(self) -> "StoryboardBuildResponse":
        ordinals = [panel.ordinal for panel in self.panels]
        if ordinals != list(range(1, len(self.panels) + 1)):
            raise ValueError("Panel ordinals must be unique and contiguous from 1.")
        return self


class StoryboardPanel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    scene_id: str = Field(min_length=1)
    ordinal: int = Field(ge=1)
    shot_type: str = Field(min_length=1, max_length=200)
    framing: str = Field(min_length=1, max_length=500)
    action: str = Field(min_length=1, max_length=5_000)
    visual_description: str = Field(min_length=1, max_length=10_000)
    dialogue: list[DialogueLine] = Field(default_factory=list)
    character_entity_ids: list[str] = Field(default_factory=list)
    location_entity_id: str | None = None
    referenced_asset_ids: list[str] = Field(default_factory=list)
    image_prompt: str = Field(min_length=1, max_length=10_000)
    negative_prompt: str | None = Field(default=None, max_length=5_000)
    render_status: RenderStatus = RenderStatus.UNRENDERED
    status: ProductionStatus = ProductionStatus.DRAFT
