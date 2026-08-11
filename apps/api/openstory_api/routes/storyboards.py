from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from openstory.application.build_storyboard import (
    BuildStoryboardService,
    StoryboardSceneNotFoundError,
    StoryboardValidationError,
)
from openstory.application.render_storyboard import (
    RenderOutputError,
    RenderStoryboardService,
    RenderTargetNotFoundError,
)
from openstory.application.run_job import RunJobService
from openstory.domain.assets import RenderVersion
from openstory.domain.jobs import JobKind, JobRunResult
from openstory.domain.status import (
    InvalidStatusTransitionError,
    LockedArtifactError,
    ProductionStatus,
    require_transition,
)
from openstory.domain.storyboard import StoryboardPanel
from openstory.persistence.repositories import StoryboardReplacementError
from openstory.services.workspace import UnsafeWorkspacePathError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from openstory_api.dependencies import (
    ImageProviderDependency,
    RepositoryDependency,
    TextProviderDependency,
    WorkspaceDependency,
)

router = APIRouter(tags=["storyboards"])


class PanelStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ProductionStatus


class RenderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width: int = Field(default=768, ge=64, le=4_096)
    height: int = Field(default=1024, ge=64, le=4_096)
    seed: int | None = Field(default=None, ge=0, le=2_147_483_647)


class SceneRenderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width: int = Field(default=768, ge=64, le=4_096)
    height: int = Field(default=1024, ge=64, le=4_096)


@router.post(
    "/scenes/{scene_id}/storyboard",
    response_model=JobRunResult[list[StoryboardPanel]],
)
async def build_storyboard(
    scene_id: str,
    repository: RepositoryDependency,
    text_provider: TextProviderDependency,
) -> JobRunResult[list[StoryboardPanel]]:
    scene = repository.get_scene(scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found.")
    episode = repository.get_episode(scene.episode_id)
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found.")

    async def operation() -> list[StoryboardPanel]:
        return await BuildStoryboardService(repository, text_provider).execute(scene_id)

    try:
        return await RunJobService(repository).run(
            episode.project_id,
            JobKind.STORYBOARD_BUILD,
            operation,
            progress_total=1,
        )
    except StoryboardSceneNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except StoryboardReplacementError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except (StoryboardValidationError, ValidationError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.get("/scenes/{scene_id}/storyboard", response_model=list[StoryboardPanel])
def list_storyboard(
    scene_id: str,
    repository: RepositoryDependency,
) -> list[StoryboardPanel]:
    if repository.get_scene(scene_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found.")
    return repository.list_storyboard_panels(scene_id)


@router.patch("/panels/{panel_id}/status", response_model=StoryboardPanel)
def update_panel_status(
    panel_id: str,
    request: PanelStatusUpdateRequest,
    repository: RepositoryDependency,
) -> StoryboardPanel:
    panel = repository.get_storyboard_panel(panel_id)
    if panel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storyboard panel not found.",
        )
    try:
        require_transition(panel.status, request.status)
    except InvalidStatusTransitionError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return repository.update_panel_status(panel_id, request.status)


@router.post(
    "/panels/{panel_id}/render",
    response_model=JobRunResult[RenderVersion],
)
async def render_panel(
    panel_id: str,
    repository: RepositoryDependency,
    workspace_manager: WorkspaceDependency,
    image_provider: ImageProviderDependency,
    request: RenderRequest | None = None,
) -> JobRunResult[RenderVersion]:
    panel = repository.get_storyboard_panel(panel_id)
    if panel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storyboard panel not found.",
        )
    scene = repository.get_scene(panel.scene_id)
    episode = repository.get_episode(scene.episode_id) if scene is not None else None
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found.")
    options = request or RenderRequest()

    async def operation() -> RenderVersion:
        return await RenderStoryboardService(
            repository,
            workspace_manager,
            image_provider,
        ).render_panel(
            panel_id,
            width=options.width,
            height=options.height,
            seed=options.seed,
        )

    try:
        return await RunJobService(repository).run(
            episode.project_id,
            JobKind.IMAGE_RENDER,
            operation,
            progress_total=1,
        )
    except LockedArtifactError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except RenderTargetNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except RenderOutputError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.post(
    "/scenes/{scene_id}/render",
    response_model=JobRunResult[list[RenderVersion]],
)
async def render_scene(
    scene_id: str,
    repository: RepositoryDependency,
    workspace_manager: WorkspaceDependency,
    image_provider: ImageProviderDependency,
    request: SceneRenderRequest | None = None,
) -> JobRunResult[list[RenderVersion]]:
    scene = repository.get_scene(scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found.")
    episode = repository.get_episode(scene.episode_id)
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found.")
    panels = repository.list_storyboard_panels(scene_id)
    options = request or SceneRenderRequest()

    async def operation() -> list[RenderVersion]:
        return await RenderStoryboardService(
            repository,
            workspace_manager,
            image_provider,
        ).render_scene(
            scene_id,
            width=options.width,
            height=options.height,
        )

    try:
        return await RunJobService(repository).run(
            episode.project_id,
            JobKind.IMAGE_RENDER,
            operation,
            progress_total=len(panels),
        )
    except LockedArtifactError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except RenderTargetNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except RenderOutputError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.get("/renders/{render_id}/file", response_class=FileResponse)
def get_render_file(
    render_id: str,
    repository: RepositoryDependency,
    workspace_manager: WorkspaceDependency,
) -> FileResponse:
    render = repository.get_render_version(render_id)
    if render is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render not found.")
    panel = repository.get_storyboard_panel(render.panel_id)
    scene = repository.get_scene(panel.scene_id) if panel is not None else None
    episode = repository.get_episode(scene.episode_id) if scene is not None else None
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found.")
    try:
        output_path = workspace_manager.resolve_project_file(
            episode.project_id,
            render.output_path,
        )
    except UnsafeWorkspacePathError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    if not output_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render file not found.")
    return FileResponse(output_path, media_type="image/png", filename=output_path.name)


@router.patch("/renders/{render_id}/status", response_model=RenderVersion)
def update_render_status(
    render_id: str,
    request: PanelStatusUpdateRequest,
    repository: RepositoryDependency,
) -> RenderVersion:
    render = repository.get_render_version(render_id)
    if render is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Render not found.")
    try:
        require_transition(render.status, request.status)
    except InvalidStatusTransitionError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return repository.update_render_status(render_id, request.status)
