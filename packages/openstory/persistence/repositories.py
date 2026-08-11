from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from openstory.domain.canon import (
    CanonEntity,
    CanonFact,
    EntityKind,
    ExtractedEntity,
)
from openstory.domain.ids import new_id
from openstory.domain.jobs import Job, JobKind, JobStatus
from openstory.domain.project import Project, TargetFormat
from openstory.domain.source import SourceChunk, SourceDocument
from openstory.persistence.models import (
    CanonEntityRecord,
    CanonFactRecord,
    JobRecord,
    ProjectRecord,
    SourceChunkRecord,
    SourceDocumentRecord,
)


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


def _canon_entity_from_record(record: CanonEntityRecord) -> CanonEntity:
    return CanonEntity(
        id=record.id,
        project_id=record.project_id,
        kind=EntityKind(record.kind),
        canonical_name=record.canonical_name,
        aliases=record.aliases,
        summary=record.summary,
        attributes=record.attributes,
    )


def _canon_fact_from_record(record: CanonFactRecord) -> CanonFact:
    return CanonFact(
        id=record.id,
        project_id=record.project_id,
        subject_entity_id=record.subject_entity_id,
        predicate=record.predicate,
        object_entity_id=record.object_entity_id,
        value=record.value,
        valid_from_ordinal=record.valid_from_ordinal,
        valid_to_ordinal=record.valid_to_ordinal,
        source_chunk_id=record.source_chunk_id,
        evidence=record.evidence,
        confidence=record.confidence,
    )


def _job_from_record(record: JobRecord) -> Job:
    return Job(
        id=record.id,
        project_id=record.project_id,
        kind=JobKind(record.kind),
        status=JobStatus(record.status),
        progress_current=record.progress_current,
        progress_total=record.progress_total,
        error=record.error,
        created_at=_aware(record.created_at),
        updated_at=_aware(record.updated_at),
    )


def normalize_entity_name(value: str) -> str:
    return " ".join(value.casefold().split())


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

    def resolve_entity(
        self,
        project_id: str,
        candidate: ExtractedEntity,
    ) -> CanonEntity:
        normalized_candidate = normalize_entity_name(candidate.canonical_name)
        records = list(
            self.session.scalars(
                select(CanonEntityRecord)
                .where(CanonEntityRecord.project_id == project_id)
                .order_by(CanonEntityRecord.id)
            )
        )
        for record in records:
            if record.normalized_name == normalized_candidate:
                return _canon_entity_from_record(record)
        for record in records:
            normalized_aliases = {normalize_entity_name(alias) for alias in record.aliases}
            if normalized_candidate in normalized_aliases:
                return _canon_entity_from_record(record)

        entity = CanonEntity(
            id=new_id(),
            project_id=project_id,
            kind=candidate.kind,
            canonical_name=candidate.canonical_name,
            aliases=candidate.aliases,
            summary=candidate.summary,
            attributes=candidate.attributes,
        )
        self.session.add(
            CanonEntityRecord(
                id=entity.id,
                project_id=project_id,
                kind=entity.kind.value,
                canonical_name=entity.canonical_name,
                normalized_name=normalized_candidate,
                aliases=entity.aliases,
                summary=entity.summary,
                attributes=entity.attributes,
            )
        )
        self.session.flush()
        return entity

    def add_canon_fact(self, fact: CanonFact) -> CanonFact:
        self.session.add(
            CanonFactRecord(
                id=fact.id,
                project_id=fact.project_id,
                subject_entity_id=fact.subject_entity_id,
                predicate=fact.predicate,
                object_entity_id=fact.object_entity_id,
                value=fact.value,
                valid_from_ordinal=fact.valid_from_ordinal,
                valid_to_ordinal=fact.valid_to_ordinal,
                source_chunk_id=fact.source_chunk_id,
                evidence=fact.evidence,
                confidence=fact.confidence,
            )
        )
        self.session.flush()
        return fact

    def list_canon_entities(self, project_id: str) -> list[CanonEntity]:
        records = self.session.scalars(
            select(CanonEntityRecord)
            .where(CanonEntityRecord.project_id == project_id)
            .order_by(CanonEntityRecord.normalized_name, CanonEntityRecord.id)
        )
        return [_canon_entity_from_record(record) for record in records]

    def list_canon_facts(self, project_id: str) -> list[CanonFact]:
        records = self.session.scalars(
            select(CanonFactRecord)
            .where(CanonFactRecord.project_id == project_id)
            .order_by(
                CanonFactRecord.source_chunk_id,
                CanonFactRecord.predicate,
                CanonFactRecord.id,
            )
        )
        return [_canon_fact_from_record(record) for record in records]

    def add_job(self, job: Job) -> Job:
        self.session.add(
            JobRecord(
                id=job.id,
                project_id=job.project_id,
                kind=job.kind.value,
                status=job.status.value,
                progress_current=job.progress_current,
                progress_total=job.progress_total,
                error=job.error,
                created_at=job.created_at,
                updated_at=job.updated_at,
            )
        )
        self.session.commit()
        return job

    def update_job(self, job: Job) -> Job:
        record = self.session.get(JobRecord, job.id)
        if record is None:
            raise LookupError("Job not found.")
        record.status = job.status.value
        record.progress_current = job.progress_current
        record.progress_total = job.progress_total
        record.error = job.error
        record.updated_at = job.updated_at
        self.session.commit()
        return job

    def get_job(self, job_id: str) -> Job | None:
        record = self.session.get(JobRecord, job_id)
        return _job_from_record(record) if record is not None else None

    def list_jobs(self, project_id: str) -> list[Job]:
        records = self.session.scalars(
            select(JobRecord)
            .where(JobRecord.project_id == project_id)
            .order_by(JobRecord.created_at, JobRecord.id)
        )
        return [_job_from_record(record) for record in records]

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
