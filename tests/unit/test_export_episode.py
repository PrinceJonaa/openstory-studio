from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

import pytest
import pytest_asyncio
from openstory.application.adapt_episode import AdaptEpisodeService
from openstory.application.build_storyboard import BuildStoryboardService
from openstory.application.create_project import CreateProjectService
from openstory.application.export_episode import (
    ExportBundle,
    ExportEpisodeService,
    ExportMissingRenderError,
)
from openstory.application.extract_canon import ExtractCanonService
from openstory.application.ingest_source import IngestSourceService
from openstory.application.render_storyboard import RenderStoryboardService
from openstory.domain.adaptation import Episode, Scene
from openstory.domain.assets import RenderVersion
from openstory.domain.project import Project, ProjectCreate
from openstory.domain.status import ProductionStatus
from openstory.domain.storyboard import StoryboardPanel
from openstory.persistence.db import create_db_engine, init_db, make_session_factory
from openstory.persistence.repositories import OpenStoryRepository
from openstory.providers.image.placeholder import PlaceholderImageProvider
from openstory.providers.text.mock import MockTextProvider
from openstory.services.workspace import WorkspaceManager


@dataclass
class ExportHarness:
    repository: OpenStoryRepository
    workspace: WorkspaceManager
    project: Project
    episode: Episode
    scenes: list[Scene]
    panels: list[StoryboardPanel]
    renders: list[RenderVersion]
    renderer: RenderStoryboardService


@pytest_asyncio.fixture
async def export_harness(tmp_path: Path) -> AsyncIterator[ExportHarness]:
    engine = create_db_engine(f"sqlite+pysqlite:///{tmp_path / 'export.db'}")
    init_db(engine)
    session_factory = make_session_factory(engine)
    workspace = WorkspaceManager(tmp_path / "workspaces")

    with session_factory() as session:
        repository = OpenStoryRepository(session)
        project = CreateProjectService(repository, workspace).execute(
            ProjectCreate(name="The Glass Orchard", target_format="storyboard")
        )
        fixture = Path("tests/fixtures/glass_orchard.md")
        ingestion = IngestSourceService(repository, workspace).execute(
            project.id,
            fixture.name,
            fixture.read_bytes(),
        )
        text_provider = MockTextProvider()
        await ExtractCanonService(repository, text_provider).execute(project.id)
        detail = await AdaptEpisodeService(repository, text_provider).execute(
            project.id,
            [chunk.id for chunk in ingestion.chunks],
            1,
            project.target_format,
        )
        panels = await BuildStoryboardService(repository, text_provider).execute(
            detail.scenes[-1].id
        )
        renderer = RenderStoryboardService(
            repository,
            workspace,
            PlaceholderImageProvider(),
        )
        renders = [
            await renderer.render_panel(panel.id, width=320, height=480)
            for panel in panels
        ]
        yield ExportHarness(
            repository=repository,
            workspace=workspace,
            project=project,
            episode=detail.episode,
            scenes=detail.scenes,
            panels=panels,
            renders=renders,
            renderer=renderer,
        )

    engine.dispose()


@pytest.mark.asyncio
async def test_export_prefers_locked_then_approved_then_latest_draft(
    export_harness: ExportHarness,
) -> None:
    panel = export_harness.panels[0]
    approved = export_harness.renders[0]
    export_harness.repository.update_render_status(approved.id, ProductionStatus.REVIEW)
    approved = export_harness.repository.update_render_status(
        approved.id,
        ProductionStatus.APPROVED,
    )
    draft = await export_harness.renderer.render_panel(panel.id, width=320, height=480)
    locked = await export_harness.renderer.render_panel(panel.id, width=320, height=480)
    export_harness.repository.update_render_status(locked.id, ProductionStatus.REVIEW)
    export_harness.repository.update_render_status(locked.id, ProductionStatus.APPROVED)
    locked = export_harness.repository.update_render_status(
        locked.id,
        ProductionStatus.LOCKED,
    )

    assert export_harness.repository.select_export_render(panel.id) == locked

    Path(locked.output_path).unlink()
    assert export_harness.repository.select_export_render(panel.id) == approved
    assert draft.version > approved.version


def test_export_is_versioned_and_round_trips_domain_json(
    export_harness: ExportHarness,
) -> None:
    service = ExportEpisodeService(export_harness.repository, export_harness.workspace)

    first = service.execute(export_harness.project.id, export_harness.episode.id)
    second = service.execute(export_harness.project.id, export_harness.episode.id)

    first_root = Path(first.output_path)
    second_root = Path(second.output_path)
    assert first.version == 1
    assert second.version == 2
    assert first_root.name == "v001"
    assert second_root.name == "v002"
    bundle = ExportBundle.model_validate_json(
        (first_root / "episode.json").read_text(encoding="utf-8")
    )
    assert bundle.project == export_harness.project
    assert bundle.episode == export_harness.episode
    assert [scene.ordinal for scene in bundle.scenes] == [1, 2]
    assert [panel.ordinal for panel in bundle.panels] == list(range(1, 7))
    assert [render.id for render in bundle.renders] == first.manifest.render_version_ids
    assert all(Path(render.output_path).is_file() for render in export_harness.renders)


def test_export_markdown_preserves_scene_and_panel_order(
    export_harness: ExportHarness,
) -> None:
    result = ExportEpisodeService(
        export_harness.repository,
        export_harness.workspace,
    ).execute(export_harness.project.id, export_harness.episode.id)

    markdown = (Path(result.output_path) / "episode.md").read_text(encoding="utf-8")
    assert markdown.index("## Scene 1") < markdown.index("## Scene 2")
    assert markdown.index("### Panel 1") < markdown.index("### Panel 6")
    assert "![Panel 1](storyboard/panel-0001.png)" in markdown
    assert "**Dialogue:**" in markdown


def test_export_requires_a_render_for_every_storyboard_panel(
    export_harness: ExportHarness,
) -> None:
    missing = export_harness.renders[0]
    Path(missing.output_path).unlink()

    with pytest.raises(ExportMissingRenderError, match="Panel 1.*render"):
        ExportEpisodeService(
            export_harness.repository,
            export_harness.workspace,
        ).execute(export_harness.project.id, export_harness.episode.id)
