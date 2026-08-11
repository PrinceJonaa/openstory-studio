from fastapi import APIRouter, HTTPException, status
from openstory.application.build_storyboard import (
    BuildStoryboardService,
    StoryboardSceneNotFoundError,
    StoryboardValidationError,
)
from openstory.application.run_job import RunJobService
from openstory.domain.jobs import JobKind, JobRunResult
from openstory.domain.status import (
    InvalidStatusTransitionError,
    ProductionStatus,
    require_transition,
)
from openstory.domain.storyboard import StoryboardPanel
from openstory.persistence.repositories import StoryboardReplacementError
from pydantic import BaseModel, ConfigDict, ValidationError

from openstory_api.dependencies import RepositoryDependency, TextProviderDependency

router = APIRouter(tags=["storyboards"])


class PanelStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ProductionStatus


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
