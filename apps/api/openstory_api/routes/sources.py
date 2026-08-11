from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from openstory.application.ingest_source import (
    DuplicateSourceError,
    IngestSourceService,
    ProjectNotFoundError,
)
from openstory.domain.source import SourceChunk, SourceDocument, SourceIngestionResult
from openstory.services.source_reader import SourceReadError

from openstory_api.dependencies import RepositoryDependency, WorkspaceDependency

router = APIRouter(prefix="/projects/{project_id}", tags=["sources"])


@router.post("/sources", response_model=SourceIngestionResult, status_code=status.HTTP_201_CREATED)
async def upload_source(
    project_id: str,
    file: Annotated[UploadFile, File()],
    repository: RepositoryDependency,
    workspace_manager: WorkspaceDependency,
) -> SourceIngestionResult:
    content = await file.read()
    await file.close()
    try:
        return IngestSourceService(repository, workspace_manager).execute(
            project_id,
            file.filename or "source.txt",
            content,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except DuplicateSourceError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except SourceReadError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/sources", response_model=list[SourceDocument])
def list_sources(
    project_id: str,
    repository: RepositoryDependency,
) -> list[SourceDocument]:
    if repository.get_project(project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return repository.list_source_documents(project_id)


@router.get("/chunks", response_model=list[SourceChunk])
def list_chunks(
    project_id: str,
    repository: RepositoryDependency,
) -> list[SourceChunk]:
    if repository.get_project(project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return repository.list_source_chunks(project_id)

