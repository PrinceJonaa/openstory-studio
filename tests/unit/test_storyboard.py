from pathlib import Path

import pytest
from openstory.application.create_project import CreateProjectService
from openstory.application.ingest_source import IngestSourceService
from openstory.domain.adaptation import Episode, Scene
from openstory.domain.ids import new_id
from openstory.domain.project import ProjectCreate
from openstory.domain.storyboard import (
    DialogueLine,
    PanelDraft,
    StoryboardBuildResponse,
    StoryboardPanel,
)
from openstory.persistence.db import create_db_engine, init_db, make_session_factory
from openstory.persistence.repositories import OpenStoryRepository
from openstory.services.workspace import WorkspaceManager
from pydantic import ValidationError


def panel_draft(ordinal: int) -> PanelDraft:
    return PanelDraft(
        ordinal=ordinal,
        shot_type="wide",
        framing="establishing",
        action="Lira approaches the gate.",
        visual_description="A ward-bound gate rises over the causeway.",
        image_prompt="Monochrome storyboard of Lira approaching a ward-bound gate.",
    )


def test_storyboard_requires_contiguous_panel_ordinals() -> None:
    with pytest.raises(ValidationError):
        StoryboardBuildResponse(panels=[panel_draft(1), panel_draft(3)])


def test_storyboard_requires_between_one_and_twenty_four_panels() -> None:
    with pytest.raises(ValidationError):
        StoryboardBuildResponse(panels=[])
    with pytest.raises(ValidationError):
        StoryboardBuildResponse(panels=[panel_draft(index) for index in range(1, 26)])


def test_storyboard_rejects_blank_production_fields() -> None:
    with pytest.raises(ValidationError):
        PanelDraft(
            ordinal=1,
            shot_type="wide",
            framing="establishing",
            action="   ",
            visual_description="A gate.",
            image_prompt="A gate storyboard.",
        )


def test_storyboard_panel_round_trips_through_db(tmp_path: Path) -> None:
    engine = create_db_engine(f"sqlite+pysqlite:///{tmp_path / 'storyboard.db'}")
    init_db(engine)
    session_factory = make_session_factory(engine)
    workspace = WorkspaceManager(tmp_path / "workspaces")

    with session_factory() as session:
        repository = OpenStoryRepository(session)
        project = CreateProjectService(repository, workspace).execute(
            ProjectCreate(name="Storyboard Story", target_format="storyboard")
        )
        ingestion = IngestSourceService(repository, workspace).execute(
            project.id,
            "story.txt",
            b"Chapter 1\nLira approaches the gate.",
        )
        episode = Episode(
            id=new_id(),
            project_id=project.id,
            number=1,
            title="The Gate",
            source_chunk_ids=[ingestion.chunks[0].id],
            logline="Lira approaches a guarded gate.",
            adaptation_notes="Omissions: none. Reordering: none.",
        )
        scene = Scene(
            id=new_id(),
            episode_id=episode.id,
            ordinal=1,
            title="Approach",
            purpose="Establish the obstacle.",
            summary="Lira approaches the gate.",
        )
        repository.add_episode(episode, [scene])
        panel = StoryboardPanel(
            id=new_id(),
            scene_id=scene.id,
            ordinal=1,
            shot_type="medium",
            framing="eye-level",
            action="Lira stops.",
            visual_description="Lira stops before the etched seals.",
            dialogue=[
                DialogueLine(
                    speaker_entity_id="lira-id",
                    speaker_name="Lira",
                    text="We need to cross.",
                )
            ],
            character_entity_ids=["lira-id"],
            location_entity_id="gate-id",
            referenced_asset_ids=["asset-v1"],
            image_prompt="Storyboard, Lira before glass-etched gate seals.",
            negative_prompt="photorealistic, text artifacts",
        )

        repository.replace_draft_storyboard(scene.id, [panel])
        restored = repository.list_storyboard_panels(scene.id)

        assert restored == [panel]

    engine.dispose()
