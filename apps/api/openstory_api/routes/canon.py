from fastapi import APIRouter, HTTPException, status
from openstory.application.extract_canon import (
    ExtractCanonService,
    ExtractionValidationError,
    SourceChunkSelectionError,
)
from openstory.application.run_job import RunJobService
from openstory.domain.canon import CanonEntity, CanonExtractionResult, CanonFact
from openstory.domain.jobs import JobKind, JobRunResult
from pydantic import BaseModel, ConfigDict, ValidationError

from openstory_api.dependencies import RepositoryDependency, TextProviderDependency

router = APIRouter(tags=["canon"])


class CanonExtractRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_ids: list[str] | None = None


@router.post(
    "/projects/{project_id}/canon/extract",
    response_model=JobRunResult[CanonExtractionResult],
)
async def extract_canon(
    project_id: str,
    repository: RepositoryDependency,
    text_provider: TextProviderDependency,
    request: CanonExtractRequest | None = None,
) -> JobRunResult[CanonExtractionResult]:
    if repository.get_project(project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    chunk_ids = request.chunk_ids if request is not None else None
    progress_total = (
        len(repository.list_source_chunks(project_id))
        if chunk_ids is None
        else len(set(chunk_ids))
    )

    async def operation() -> CanonExtractionResult:
        return await ExtractCanonService(repository, text_provider).execute(
            project_id,
            chunk_ids,
        )

    try:
        return await RunJobService(repository).run(
            project_id,
            JobKind.CANON_EXTRACT,
            operation,
            progress_total,
        )
    except SourceChunkSelectionError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (ExtractionValidationError, ValidationError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.get("/projects/{project_id}/entities", response_model=list[CanonEntity])
def list_entities(
    project_id: str,
    repository: RepositoryDependency,
) -> list[CanonEntity]:
    if repository.get_project(project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return repository.list_canon_entities(project_id)


@router.get("/projects/{project_id}/facts", response_model=list[CanonFact])
def list_facts(
    project_id: str,
    repository: RepositoryDependency,
) -> list[CanonFact]:
    if repository.get_project(project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return repository.list_canon_facts(project_id)
