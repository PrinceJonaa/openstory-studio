from fastapi import APIRouter, HTTPException, status
from openstory.application.create_project import CreateProjectService
from openstory.domain.project import Project, ProjectCreate
from openstory.persistence.repositories import DuplicateProjectSlugError

from openstory_api.dependencies import RepositoryDependency, WorkspaceDependency

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(
    command: ProjectCreate,
    repository: RepositoryDependency,
    workspace_manager: WorkspaceDependency,
) -> Project:
    try:
        return CreateProjectService(repository, workspace_manager).execute(command)
    except DuplicateProjectSlugError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("", response_model=list[Project])
def list_projects(
    repository: RepositoryDependency,
) -> list[Project]:
    return repository.list_projects()


@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: str,
    repository: RepositoryDependency,
) -> Project:
    project = repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project
