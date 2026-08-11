from fastapi import APIRouter, HTTPException, status
from openstory.application.adapt_episode import (
    AdaptationChunkSelectionError,
    AdaptationValidationError,
    AdaptEpisodeService,
)
from openstory.application.run_job import RunJobService
from openstory.domain.adaptation import Episode, EpisodeDetail, Scene
from openstory.domain.jobs import JobKind, JobRunResult
from openstory.domain.project import TargetFormat
from openstory.domain.status import (
    InvalidStatusTransitionError,
    ProductionStatus,
    require_transition,
)
from openstory.persistence.repositories import DuplicateEpisodeNumberError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from openstory_api.dependencies import RepositoryDependency, TextProviderDependency

router = APIRouter(tags=["episodes"])


class AdaptEpisodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_chunk_ids: list[str] = Field(min_length=1)
    number: int = Field(ge=1)
    target_format: TargetFormat


class StatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ProductionStatus


@router.post(
    "/projects/{project_id}/episodes/adapt",
    response_model=JobRunResult[EpisodeDetail],
)
async def adapt_episode(
    project_id: str,
    request: AdaptEpisodeRequest,
    repository: RepositoryDependency,
    text_provider: TextProviderDependency,
) -> JobRunResult[EpisodeDetail]:
    if repository.get_project(project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    async def operation() -> EpisodeDetail:
        return await AdaptEpisodeService(repository, text_provider).execute(
            project_id=project_id,
            source_chunk_ids=request.source_chunk_ids,
            number=request.number,
            target_format=request.target_format,
        )

    try:
        return await RunJobService(repository).run(
            project_id,
            JobKind.EPISODE_ADAPT,
            operation,
            progress_total=1,
        )
    except AdaptationChunkSelectionError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except DuplicateEpisodeNumberError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except (AdaptationValidationError, ValidationError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.get("/projects/{project_id}/episodes", response_model=list[Episode])
def list_episodes(
    project_id: str,
    repository: RepositoryDependency,
) -> list[Episode]:
    if repository.get_project(project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return repository.list_episodes(project_id)


@router.get("/episodes/{episode_id}", response_model=EpisodeDetail)
def get_episode(
    episode_id: str,
    repository: RepositoryDependency,
) -> EpisodeDetail:
    episode = repository.get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found.")
    return EpisodeDetail(episode=episode, scenes=repository.list_scenes(episode_id))


@router.patch("/episodes/{episode_id}/status", response_model=Episode)
def update_episode_status(
    episode_id: str,
    request: StatusUpdateRequest,
    repository: RepositoryDependency,
) -> Episode:
    episode = repository.get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found.")
    try:
        require_transition(episode.status, request.status)
    except InvalidStatusTransitionError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return repository.update_episode_status(episode_id, request.status)


@router.patch("/scenes/{scene_id}/status", response_model=Scene)
def update_scene_status(
    scene_id: str,
    request: StatusUpdateRequest,
    repository: RepositoryDependency,
) -> Scene:
    scene = repository.get_scene(scene_id)
    if scene is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found.")
    try:
        require_transition(scene.status, request.status)
    except InvalidStatusTransitionError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return repository.update_scene_status(scene_id, request.status)
