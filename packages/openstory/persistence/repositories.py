from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from openstory.domain.adaptation import Episode, Scene
from openstory.domain.assets import RenderVersion
from openstory.domain.canon import (
    CanonEntity,
    CanonFact,
    CanonSnapshot,
    EntityKind,
    ExtractedEntity,
)
from openstory.domain.ids import new_id
from openstory.domain.jobs import Job, JobKind, JobStatus
from openstory.domain.project import Project, TargetFormat
from openstory.domain.source import SourceChunk, SourceDocument
from openstory.domain.status import ProductionStatus
from openstory.domain.storyboard import (
    DialogueLine,
    RenderStatus,
    StoryboardPanel,
)
from openstory.persistence.models import (
    CanonEntityRecord,
    CanonFactRecord,
    EpisodeRecord,
    JobRecord,
    ProjectRecord,
    RenderVersionRecord,
    SceneRecord,
    SourceChunkRecord,
    SourceDocumentRecord,
    StoryboardPanelRecord,
)


class DuplicateProjectSlugError(ValueError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"A project with slug '{slug}' already exists.")
        self.slug = slug


class DuplicateSourceHashError(ValueError):
    def __init__(self, sha256: str) -> None:
        super().__init__("This source content is already imported in the project.")
        self.sha256 = sha256


class DuplicateEpisodeNumberError(ValueError):
    def __init__(self, number: int) -> None:
        super().__init__(f"Episode number {number} already exists in this project.")
        self.number = number


class StoryboardReplacementError(ValueError):
    pass


class RenderVersionCollisionError(ValueError):
    pass


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


def _episode_from_record(record: EpisodeRecord) -> Episode:
    return Episode(
        id=record.id,
        project_id=record.project_id,
        number=record.number,
        title=record.title,
        source_chunk_ids=record.source_chunk_ids,
        logline=record.logline,
        adaptation_notes=record.adaptation_notes,
        status=ProductionStatus(record.status),
    )


def _scene_from_record(record: SceneRecord) -> Scene:
    return Scene(
        id=record.id,
        episode_id=record.episode_id,
        ordinal=record.ordinal,
        title=record.title,
        purpose=record.purpose,
        location_entity_id=record.location_entity_id,
        character_entity_ids=record.character_entity_ids,
        summary=record.summary,
        status=ProductionStatus(record.status),
    )


def _storyboard_panel_from_record(record: StoryboardPanelRecord) -> StoryboardPanel:
    return StoryboardPanel(
        id=record.id,
        scene_id=record.scene_id,
        ordinal=record.ordinal,
        shot_type=record.shot_type,
        framing=record.framing,
        action=record.action,
        visual_description=record.visual_description,
        dialogue=[DialogueLine.model_validate(line) for line in record.dialogue],
        character_entity_ids=record.character_entity_ids,
        location_entity_id=record.location_entity_id,
        referenced_asset_ids=record.referenced_asset_ids,
        image_prompt=record.image_prompt,
        negative_prompt=record.negative_prompt,
        render_status=RenderStatus(record.render_status),
        status=ProductionStatus(record.status),
    )


def _render_version_from_record(record: RenderVersionRecord) -> RenderVersion:
    return RenderVersion(
        id=record.id,
        panel_id=record.panel_id,
        version=record.version,
        output_path=record.output_path,
        width=record.width,
        height=record.height,
        seed=record.seed,
        provider=record.provider,
        metadata=record.metadata_json,
        status=ProductionStatus(record.status),
        created_at=_aware(record.created_at),
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

    def get_canon_entities_by_ids(
        self,
        project_id: str,
        entity_ids: Sequence[str],
    ) -> list[CanonEntity]:
        unique_ids = set(entity_ids)
        if not unique_ids:
            return []
        records = self.session.scalars(
            select(CanonEntityRecord)
            .where(
                CanonEntityRecord.project_id == project_id,
                CanonEntityRecord.id.in_(unique_ids),
            )
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

    def get_canon_snapshot(self, project_id: str, ordinal: int) -> CanonSnapshot:
        if ordinal < 0:
            raise ValueError("Snapshot ordinal cannot be negative.")
        fact_records = list(
            self.session.scalars(
                select(CanonFactRecord)
                .where(
                    and_(
                        CanonFactRecord.project_id == project_id,
                        or_(
                            CanonFactRecord.valid_from_ordinal.is_(None),
                            CanonFactRecord.valid_from_ordinal <= ordinal,
                        ),
                        or_(
                            CanonFactRecord.valid_to_ordinal.is_(None),
                            CanonFactRecord.valid_to_ordinal >= ordinal,
                        ),
                    )
                )
                .order_by(CanonFactRecord.predicate, CanonFactRecord.id)
            )
        )
        facts = [_canon_fact_from_record(record) for record in fact_records]
        entity_ids = {
            entity_id
            for fact in facts
            for entity_id in (fact.subject_entity_id, fact.object_entity_id)
            if entity_id is not None
        }
        entity_records = (
            list(
                self.session.scalars(
                    select(CanonEntityRecord)
                    .where(
                        CanonEntityRecord.project_id == project_id,
                        CanonEntityRecord.id.in_(entity_ids),
                    )
                    .order_by(CanonEntityRecord.normalized_name, CanonEntityRecord.id)
                )
            )
            if entity_ids
            else []
        )
        return CanonSnapshot(
            project_id=project_id,
            ordinal=ordinal,
            entities=[_canon_entity_from_record(record) for record in entity_records],
            facts=facts,
        )

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

    def add_episode(
        self,
        episode: Episode,
        scenes: Sequence[Scene],
    ) -> tuple[Episode, list[Scene]]:
        self.session.add(
            EpisodeRecord(
                id=episode.id,
                project_id=episode.project_id,
                number=episode.number,
                title=episode.title,
                source_chunk_ids=episode.source_chunk_ids,
                logline=episode.logline,
                adaptation_notes=episode.adaptation_notes,
                status=episode.status.value,
            )
        )
        scene_list = list(scenes)
        self.session.add_all(
            [
                SceneRecord(
                    id=scene.id,
                    episode_id=scene.episode_id,
                    ordinal=scene.ordinal,
                    title=scene.title,
                    purpose=scene.purpose,
                    location_entity_id=scene.location_entity_id,
                    character_entity_ids=scene.character_entity_ids,
                    summary=scene.summary,
                    status=scene.status.value,
                )
                for scene in scene_list
            ]
        )
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise DuplicateEpisodeNumberError(episode.number) from error
        return episode, scene_list

    def list_episodes(self, project_id: str) -> list[Episode]:
        records = self.session.scalars(
            select(EpisodeRecord)
            .where(EpisodeRecord.project_id == project_id)
            .order_by(EpisodeRecord.number, EpisodeRecord.id)
        )
        return [_episode_from_record(record) for record in records]

    def get_episode(self, episode_id: str) -> Episode | None:
        record = self.session.get(EpisodeRecord, episode_id)
        return _episode_from_record(record) if record is not None else None

    def list_scenes(self, episode_id: str) -> list[Scene]:
        records = self.session.scalars(
            select(SceneRecord)
            .where(SceneRecord.episode_id == episode_id)
            .order_by(SceneRecord.ordinal, SceneRecord.id)
        )
        return [_scene_from_record(record) for record in records]

    def get_scene(self, scene_id: str) -> Scene | None:
        record = self.session.get(SceneRecord, scene_id)
        return _scene_from_record(record) if record is not None else None

    def update_episode_status(
        self,
        episode_id: str,
        target: ProductionStatus,
    ) -> Episode:
        record = self.session.get(EpisodeRecord, episode_id)
        if record is None:
            raise LookupError("Episode not found.")
        record.status = target.value
        self.session.commit()
        return _episode_from_record(record)

    def update_scene_status(
        self,
        scene_id: str,
        target: ProductionStatus,
    ) -> Scene:
        record = self.session.get(SceneRecord, scene_id)
        if record is None:
            raise LookupError("Scene not found.")
        record.status = target.value
        self.session.commit()
        return _scene_from_record(record)

    def replace_draft_storyboard(
        self,
        scene_id: str,
        panels: Sequence[StoryboardPanel],
    ) -> list[StoryboardPanel]:
        existing = self.list_storyboard_panels(scene_id)
        non_draft = [panel for panel in existing if panel.status is not ProductionStatus.DRAFT]
        if non_draft:
            raise StoryboardReplacementError(
                "Storyboard replacement requires every existing panel to be in draft status."
            )
        panel_list = list(panels)
        if any(panel.scene_id != scene_id for panel in panel_list):
            raise ValueError("Every storyboard panel must belong to the target scene.")
        if any(panel.status is not ProductionStatus.DRAFT for panel in panel_list):
            raise ValueError("New storyboard panels must begin in draft status.")

        self.session.execute(
            delete(StoryboardPanelRecord).where(StoryboardPanelRecord.scene_id == scene_id)
        )
        self.session.add_all(
            [
                StoryboardPanelRecord(
                    id=panel.id,
                    scene_id=panel.scene_id,
                    ordinal=panel.ordinal,
                    shot_type=panel.shot_type,
                    framing=panel.framing,
                    action=panel.action,
                    visual_description=panel.visual_description,
                    dialogue=[line.model_dump(mode="json") for line in panel.dialogue],
                    character_entity_ids=panel.character_entity_ids,
                    location_entity_id=panel.location_entity_id,
                    referenced_asset_ids=panel.referenced_asset_ids,
                    image_prompt=panel.image_prompt,
                    negative_prompt=panel.negative_prompt,
                    render_status=panel.render_status.value,
                    status=panel.status.value,
                )
                for panel in panel_list
            ]
        )
        self.session.commit()
        return panel_list

    def list_storyboard_panels(self, scene_id: str) -> list[StoryboardPanel]:
        records = self.session.scalars(
            select(StoryboardPanelRecord)
            .where(StoryboardPanelRecord.scene_id == scene_id)
            .order_by(StoryboardPanelRecord.ordinal, StoryboardPanelRecord.id)
        )
        return [_storyboard_panel_from_record(record) for record in records]

    def get_storyboard_panel(self, panel_id: str) -> StoryboardPanel | None:
        record = self.session.get(StoryboardPanelRecord, panel_id)
        return _storyboard_panel_from_record(record) if record is not None else None

    def update_panel_status(
        self,
        panel_id: str,
        target: ProductionStatus,
    ) -> StoryboardPanel:
        record = self.session.get(StoryboardPanelRecord, panel_id)
        if record is None:
            raise LookupError("Storyboard panel not found.")
        record.status = target.value
        self.session.commit()
        return _storyboard_panel_from_record(record)

    def next_render_version(self, panel_id: str) -> int:
        maximum = self.session.scalar(
            select(func.max(RenderVersionRecord.version)).where(
                RenderVersionRecord.panel_id == panel_id
            )
        )
        return int(maximum or 0) + 1

    def add_render_version(self, render: RenderVersion) -> RenderVersion:
        panel_record = self.session.get(StoryboardPanelRecord, render.panel_id)
        if panel_record is None:
            raise LookupError("Storyboard panel not found.")
        self.session.add(
            RenderVersionRecord(
                id=render.id,
                panel_id=render.panel_id,
                version=render.version,
                output_path=render.output_path,
                width=render.width,
                height=render.height,
                seed=render.seed,
                provider=render.provider,
                metadata_json=render.metadata,
                status=render.status.value,
                created_at=render.created_at,
            )
        )
        panel_record.render_status = RenderStatus.RENDERED.value
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise RenderVersionCollisionError(
                f"Render version {render.version} already exists for this panel."
            ) from error
        return render

    def list_render_versions(self, panel_id: str) -> list[RenderVersion]:
        records = self.session.scalars(
            select(RenderVersionRecord)
            .where(RenderVersionRecord.panel_id == panel_id)
            .order_by(RenderVersionRecord.version, RenderVersionRecord.id)
        )
        return [_render_version_from_record(record) for record in records]

    def get_render_version(self, render_id: str) -> RenderVersion | None:
        record = self.session.get(RenderVersionRecord, render_id)
        return _render_version_from_record(record) if record is not None else None

    def update_render_status(
        self,
        render_id: str,
        target: ProductionStatus,
    ) -> RenderVersion:
        record = self.session.get(RenderVersionRecord, render_id)
        if record is None:
            raise LookupError("Render version not found.")
        record.status = target.value
        self.session.commit()
        return _render_version_from_record(record)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
