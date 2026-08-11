from fastapi import APIRouter, HTTPException, status
from openstory.application.export_episode import (
    ExportEpisodeService,
    ExportMissingRenderError,
    ExportNotFoundError,
    ExportResult,
    ExportValidationError,
)
from openstory.application.run_job import RunJobService
from openstory.domain.jobs import JobKind, JobRunResult
from pydantic import BaseModel, ConfigDict, Field

from openstory_api.dependencies import RepositoryDependency, WorkspaceDependency

router = APIRouter(tags=["exports"])


class ExportEpisodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    episode_id: str = Field(min_length=1)


@router.post(
    "/projects/{project_id}/export",
    response_model=JobRunResult[ExportResult],
    status_code=status.HTTP_201_CREATED,
)
async def export_episode(
    project_id: str,
    request: ExportEpisodeRequest,
    repository: RepositoryDependency,
    workspace_manager: WorkspaceDependency,
) -> JobRunResult[ExportResult]:
    episode = repository.get_episode(request.episode_id)
    if episode is None or episode.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found in this project.",
        )
    panel_count = sum(
        len(repository.list_storyboard_panels(scene.id))
        for scene in repository.list_scenes(episode.id)
    )

    async def operation() -> ExportResult:
        return ExportEpisodeService(repository, workspace_manager).execute(
            project_id,
            episode.id,
        )

    try:
        return await RunJobService(repository).run(
            project_id,
            JobKind.EXPORT,
            operation,
            progress_total=panel_count,
        )
    except ExportNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ExportMissingRenderError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except ExportValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
