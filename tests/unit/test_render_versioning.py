from collections.abc import AsyncIterator
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import pytest
import pytest_asyncio
from openstory.application.adapt_episode import AdaptEpisodeService
from openstory.application.build_storyboard import BuildStoryboardService
from openstory.application.create_project import CreateProjectService
from openstory.application.extract_canon import ExtractCanonService
from openstory.application.ingest_source import IngestSourceService
from openstory.application.render_storyboard import RenderStoryboardService
from openstory.domain.assets import ImageGenerationResult, RenderVersion
from openstory.domain.project import ProjectCreate
from openstory.domain.status import LockedArtifactError, ProductionStatus
from openstory.domain.storyboard import StoryboardPanel
from openstory.persistence.db import create_db_engine, init_db, make_session_factory
from openstory.persistence.repositories import OpenStoryRepository
from openstory.providers.image.placeholder import PlaceholderImageProvider
from openstory.providers.text.mock import MockTextProvider
from openstory.services.workspace import WorkspaceManager


class RecordingImageProvider:
    def __init__(self) -> None:
        self.delegate = PlaceholderImageProvider()
        self.calls = 0

    async def generate(self, **kwargs: object) -> ImageGenerationResult:
        self.calls += 1
        return await self.delegate.generate(**kwargs)  # type: ignore[arg-type]


@dataclass
class RenderedPanel:
    repository: OpenStoryRepository
    service: RenderStoryboardService
    panel: StoryboardPanel
    provider: RecordingImageProvider
    workspace: WorkspaceManager
    project_id: str


@pytest_asyncio.fixture
async def rendered_panel(tmp_path: Path) -> AsyncIterator[RenderedPanel]:
    engine = create_db_engine(f"sqlite+pysqlite:///{tmp_path / 'render.db'}")
    init_db(engine)
    session_factory = make_session_factory(engine)
    workspace = WorkspaceManager(tmp_path / "workspaces")
    provider = RecordingImageProvider()

    with session_factory() as session:
        repository = OpenStoryRepository(session)
        project = CreateProjectService(repository, workspace).execute(
            ProjectCreate(name="The Glass Orchard", target_format="storyboard")
        )
        source = Path("tests/fixtures/glass_orchard.md")
        ingestion = IngestSourceService(repository, workspace).execute(
            project.id,
            source.name,
            source.read_bytes(),
        )
        text_provider = MockTextProvider()
        await ExtractCanonService(repository, text_provider).execute(project.id)
        adapted = await AdaptEpisodeService(repository, text_provider).execute(
            project.id,
            [chunk.id for chunk in ingestion.chunks],
            1,
            project.target_format,
        )
        panels = await BuildStoryboardService(repository, text_provider).execute(
            adapted.scenes[-1].id
        )
        yield RenderedPanel(
            repository=repository,
            service=RenderStoryboardService(repository, workspace, provider),
            panel=panels[0],
            provider=provider,
            workspace=workspace,
            project_id=project.id,
        )

    engine.dispose()


@pytest.mark.asyncio
async def test_regeneration_creates_next_version(rendered_panel: RenderedPanel) -> None:
    first = await rendered_panel.service.render_panel(rendered_panel.panel.id, seed=10)
    second = await rendered_panel.service.render_panel(rendered_panel.panel.id, seed=11)

    assert first.version == 1
    assert second.version == 2
    assert first.output_path != second.output_path
    assert Path(first.output_path).exists()
    assert Path(second.output_path).exists()
    assert "/panel-0001/v001.png" in first.output_path
    assert "/panel-0001/v002.png" in second.output_path


@pytest.mark.asyncio
async def test_approved_render_file_remains_unchanged_after_regeneration(
    rendered_panel: RenderedPanel,
) -> None:
    first = await rendered_panel.service.render_panel(rendered_panel.panel.id, seed=10)
    first_path = Path(first.output_path)
    original_hash = sha256(first_path.read_bytes()).hexdigest()
    rendered_panel.repository.update_render_status(first.id, ProductionStatus.REVIEW)
    approved = rendered_panel.repository.update_render_status(
        first.id,
        ProductionStatus.APPROVED,
    )

    second = await rendered_panel.service.render_panel(rendered_panel.panel.id, seed=11)

    assert approved.status is ProductionStatus.APPROVED
    assert second.version == 2
    assert sha256(first_path.read_bytes()).hexdigest() == original_hash


@pytest.mark.asyncio
async def test_locked_panel_rejects_render_before_invoking_provider(
    rendered_panel: RenderedPanel,
) -> None:
    for target in (
        ProductionStatus.REVIEW,
        ProductionStatus.APPROVED,
        ProductionStatus.LOCKED,
    ):
        rendered_panel.repository.update_panel_status(rendered_panel.panel.id, target)

    with pytest.raises(LockedArtifactError):
        await rendered_panel.service.render_panel(rendered_panel.panel.id)

    assert rendered_panel.provider.calls == 0
    assert rendered_panel.repository.list_render_versions(rendered_panel.panel.id) == []


def test_render_version_model_round_trip_shape() -> None:
    version = RenderVersion(
        id="render",
        panel_id="panel",
        version=1,
        output_path="/workspace/panel.png",
        width=768,
        height=1024,
        seed=7,
        provider="placeholder",
        metadata={"style": "storyboard"},
    )

    assert RenderVersion.model_validate(version.model_dump()) == version
