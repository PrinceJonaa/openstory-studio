from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from openstory.domain.project import Project, TargetFormat
from openstory.persistence.models import ProjectRecord


class DuplicateProjectSlugError(ValueError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"A project with slug '{slug}' already exists.")
        self.slug = slug


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _project_from_record(record: ProjectRecord) -> Project:
    return Project(
        id=record.id,
        name=record.name,
        slug=record.slug,
        description=record.description,
        target_format=TargetFormat(record.target_format),
        created_at=_aware(record.created_at),
        updated_at=_aware(record.updated_at),
    )


class OpenStoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_project(self, project: Project) -> Project:
        self.session.add(
            ProjectRecord(
                id=project.id,
                name=project.name,
                slug=project.slug,
                description=project.description,
                target_format=project.target_format.value,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
        )
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise DuplicateProjectSlugError(project.slug) from error
        return project

    def get_project(self, project_id: str) -> Project | None:
        record = self.session.get(ProjectRecord, project_id)
        return _project_from_record(record) if record is not None else None

    def list_projects(self) -> list[Project]:
        records = self.session.scalars(
            select(ProjectRecord).order_by(ProjectRecord.created_at, ProjectRecord.id)
        )
        return [_project_from_record(record) for record in records]

