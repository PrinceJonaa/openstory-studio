from pathlib import Path

from openstory.domain.ids import new_id
from openstory.domain.source import SourceChunk, SourceDocument, SourceIngestionResult
from openstory.persistence.repositories import (
    DuplicateSourceHashError,
    OpenStoryRepository,
)
from openstory.services.chunking import chunk_source
from openstory.services.source_reader import read_source
from openstory.services.workspace import WorkspaceManager


class ProjectNotFoundError(LookupError):
    pass


class DuplicateSourceError(ValueError):
    pass


class IngestSourceService:
    def __init__(
        self,
        repository: OpenStoryRepository,
        workspace_manager: WorkspaceManager,
    ) -> None:
        self.repository = repository
        self.workspace_manager = workspace_manager

    def execute(
        self,
        project_id: str,
        filename: str,
        content: bytes,
    ) -> SourceIngestionResult:
        if self.repository.get_project(project_id) is None:
            raise ProjectNotFoundError("Project not found.")

        source = read_source(filename, content)
        if self.repository.get_source_by_hash(project_id, source.sha256) is not None:
            raise DuplicateSourceError("This source content is already imported in the project.")

        document_id = new_id()
        final_path = self.workspace_manager.source_path(
            project_id,
            f"{document_id}-{source.filename}",
        )
        temporary_path = final_path.with_name(f".{final_path.name}.tmp")
        drafts = chunk_source(source.text, source.media_type)
        first_ordinal = self.repository.next_chunk_ordinal(project_id)
        document = SourceDocument(
            id=document_id,
            project_id=project_id,
            filename=source.filename,
            media_type=source.media_type,
            sha256=source.sha256,
            workspace_path=str(final_path),
        )
        chunks = [
            SourceChunk(
                id=new_id(),
                document_id=document_id,
                ordinal=first_ordinal + index,
                heading=draft.heading,
                text=draft.text,
                start_offset=draft.start_offset,
                end_offset=draft.end_offset,
            )
            for index, draft in enumerate(drafts)
        ]

        final_created = False
        try:
            temporary_path.write_bytes(content)
            self.repository.add_source_document(project_id, document, chunks)
            temporary_path.replace(final_path)
            final_created = True
            self.repository.commit()
        except DuplicateSourceHashError as error:
            self.repository.rollback()
            self._remove_created_files(temporary_path, final_path, final_created)
            raise DuplicateSourceError(str(error)) from error
        except Exception:
            self.repository.rollback()
            self._remove_created_files(temporary_path, final_path, final_created)
            raise

        return SourceIngestionResult(document=document, chunks=chunks)

    @staticmethod
    def _remove_created_files(
        temporary_path: Path,
        final_path: Path,
        final_created: bool,
    ) -> None:
        temporary_path.unlink(missing_ok=True)
        if final_created:
            final_path.unlink(missing_ok=True)

