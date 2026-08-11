from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from openstory.domain.project import Project, TargetFormat
from openstory.domain.source import SourceChunk, SourceDocument
from openstory.persistence.models import ProjectRecord, SourceChunkRecord, SourceDocumentRecord


class DuplicateProjectSlugError(ValueError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"A project with slug '{slug}' already exists.")
        self.slug = slug


class DuplicateSourceHashError(ValueError):
    def __init__(self, sha256: str) -> None:
        super().__init__("This source content is already imported in the project.")
        self.sha256 = sha256


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


def _source_document_from_record(record: SourceDocumentRecord) -> SourceDocument:
    return SourceDocument(
        id=record.id,
        project_id=record.project_id,
        filename=record.filename,
        media_type=record.media_type,
        sha256=record.sha256,
        workspace_path=record.workspace_path,
    )


def _source_chunk_from_record(record: SourceChunkRecord) -> SourceChunk:
    return SourceChunk(
        id=record.id,
        document_id=record.document_id,
        ordinal=record.ordinal,
        heading=record.heading,
        text=record.text,
        start_offset=record.start_offset,
        end_offset=record.end_offset,
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

    def get_source_by_hash(self, project_id: str, sha256: str) -> SourceDocument | None:
        record = self.session.scalar(
            select(SourceDocumentRecord).where(
                SourceDocumentRecord.project_id == project_id,
                SourceDocumentRecord.sha256 == sha256,
            )
        )
        return _source_document_from_record(record) if record is not None else None

    def next_chunk_ordinal(self, project_id: str) -> int:
        maximum = self.session.scalar(
            select(func.max(SourceChunkRecord.ordinal)).where(
                SourceChunkRecord.project_id == project_id
            )
        )
        return int(maximum or 0) + 1

    def add_source_document(
        self,
        project_id: str,
        document: SourceDocument,
        chunks: list[SourceChunk],
    ) -> None:
        self.session.add(
            SourceDocumentRecord(
                id=document.id,
                project_id=project_id,
                filename=document.filename,
                media_type=document.media_type,
                sha256=document.sha256,
                workspace_path=document.workspace_path,
            )
        )
        self.session.add_all(
            [
                SourceChunkRecord(
                    id=chunk.id,
                    project_id=project_id,
                    document_id=chunk.document_id,
                    ordinal=chunk.ordinal,
                    heading=chunk.heading,
                    text=chunk.text,
                    start_offset=chunk.start_offset,
                    end_offset=chunk.end_offset,
                )
                for chunk in chunks
            ]
        )
        try:
            self.session.flush()
        except IntegrityError as error:
            self.session.rollback()
            raise DuplicateSourceHashError(document.sha256) from error

    def list_source_documents(self, project_id: str) -> list[SourceDocument]:
        records = self.session.scalars(
            select(SourceDocumentRecord)
            .where(SourceDocumentRecord.project_id == project_id)
            .order_by(SourceDocumentRecord.filename, SourceDocumentRecord.id)
        )
        return [_source_document_from_record(record) for record in records]

    def list_source_chunks(self, project_id: str) -> list[SourceChunk]:
        records = self.session.scalars(
            select(SourceChunkRecord)
            .where(SourceChunkRecord.project_id == project_id)
            .order_by(SourceChunkRecord.ordinal)
        )
        return [_source_chunk_from_record(record) for record in records]

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

