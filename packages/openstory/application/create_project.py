from openstory.domain.ids import new_id
from openstory.domain.project import Project, ProjectCreate, slugify, utc_now
from openstory.persistence.repositories import OpenStoryRepository
from openstory.services.workspace import WorkspaceManager


class CreateProjectService:
    def __init__(
        self,
        repository: OpenStoryRepository,
        workspace_manager: WorkspaceManager,
    ) -> None:
        self.repository = repository
        self.workspace_manager = workspace_manager

    def execute(self, command: ProjectCreate) -> Project:
        timestamp = utc_now()
        project = Project(
            id=new_id(),
            name=command.name,
            slug=slugify(command.name),
            description=command.description,
            target_format=command.target_format,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.workspace_manager.create_project(project.id)
        try:
            return self.repository.add_project(project)
        except Exception:
            self.workspace_manager.remove_project(project.id)
            raise

