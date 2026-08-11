from pathlib import Path

from openstory.domain.canon import (
    CanonEntity,
    CanonExtractionResponse,
    CanonExtractionResult,
    CanonFact,
    ExtractedEntity,
)
from openstory.domain.ids import new_id
from openstory.domain.source import SourceChunk
from openstory.persistence.repositories import OpenStoryRepository
from openstory.providers.text.base import TextGenerationProvider

CANON_PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "canon_extract.md"


class ProjectNotFoundError(LookupError):
    pass


class SourceChunkSelectionError(LookupError):
    pass


class ExtractionValidationError(ValueError):
    pass


class ExtractCanonService:
    def __init__(
        self,
        repository: OpenStoryRepository,
        provider: TextGenerationProvider,
    ) -> None:
        self.repository = repository
        self.provider = provider

    async def execute(
        self,
        project_id: str,
        chunk_ids: list[str] | None = None,
    ) -> CanonExtractionResult:
        project = self.repository.get_project(project_id)
        if project is None:
            raise ProjectNotFoundError("Project not found.")

        chunks = self._select_chunks(project_id, chunk_ids)
        system_prompt = CANON_PROMPT_PATH.read_text(encoding="utf-8")
        resolved_entities: dict[str, CanonEntity] = {}
        persisted_facts: list[CanonFact] = []
        unresolved_references: list[str] = []

        for chunk in chunks:
            existing_entities = self.repository.list_canon_entities(project_id)
            index = ", ".join(
                f"{entity.canonical_name} ({', '.join(entity.aliases)})"
                if entity.aliases
                else entity.canonical_name
                for entity in existing_entities
            )
            response = await self.provider.generate_structured(
                system_prompt=system_prompt,
                user_prompt=(
                    f"Project: {project.name}\n"
                    f"Existing entity index: {index or '(empty)'}\n"
                    f"Source chunk ordinal: {chunk.ordinal}\n\n{chunk.text}"
                ),
                schema=CanonExtractionResponse,
            )
            by_ref = self._validate_response(chunk, response)
            ref_to_entity = {
                ref: self.repository.resolve_entity(project_id, candidate)
                for ref, candidate in by_ref.items()
            }
            for entity in ref_to_entity.values():
                resolved_entities[entity.id] = entity

            for extracted_fact in response.facts:
                fact = CanonFact(
                    id=new_id(),
                    project_id=project_id,
                    subject_entity_id=ref_to_entity[extracted_fact.subject_ref].id,
                    predicate=extracted_fact.predicate,
                    object_entity_id=(
                        ref_to_entity[extracted_fact.object_ref].id
                        if extracted_fact.object_ref is not None
                        else None
                    ),
                    value=extracted_fact.value,
                    valid_from_ordinal=extracted_fact.valid_from_ordinal,
                    valid_to_ordinal=extracted_fact.valid_to_ordinal,
                    source_chunk_id=chunk.id,
                    evidence=extracted_fact.evidence,
                    confidence=extracted_fact.confidence,
                )
                persisted_facts.append(self.repository.add_canon_fact(fact))
            unresolved_references.extend(response.unresolved_references)

        self.repository.commit()
        return CanonExtractionResult(
            project_id=project_id,
            source_chunk_ids=[chunk.id for chunk in chunks],
            entities=sorted(
                resolved_entities.values(),
                key=lambda entity: (entity.canonical_name.casefold(), entity.id),
            ),
            facts=persisted_facts,
            unresolved_references=unresolved_references,
        )

    def _select_chunks(
        self,
        project_id: str,
        chunk_ids: list[str] | None,
    ) -> list[SourceChunk]:
        available = self.repository.list_source_chunks(project_id)
        if chunk_ids is None:
            return available
        selected_ids = set(chunk_ids)
        available_ids = {chunk.id for chunk in available}
        missing_ids = sorted(selected_ids - available_ids)
        if missing_ids:
            raise SourceChunkSelectionError(
                f"Source chunks do not belong to this project: {', '.join(missing_ids)}"
            )
        return [chunk for chunk in available if chunk.id in selected_ids]

    @staticmethod
    def _validate_response(
        chunk: SourceChunk,
        response: CanonExtractionResponse,
    ) -> dict[str, ExtractedEntity]:
        by_ref: dict[str, ExtractedEntity] = {}
        for entity in response.entities:
            if entity.ref in by_ref:
                raise ExtractionValidationError(
                    f"Provider returned duplicate entity ref '{entity.ref}'."
                )
            by_ref[entity.ref] = entity

        for fact in response.facts:
            if fact.subject_ref not in by_ref:
                raise ExtractionValidationError(
                    f"Fact subject ref '{fact.subject_ref}' has no extracted entity."
                )
            if fact.object_ref is not None and fact.object_ref not in by_ref:
                raise ExtractionValidationError(
                    f"Fact object ref '{fact.object_ref}' has no extracted entity."
                )
            if fact.evidence not in chunk.text:
                raise ExtractionValidationError(
                    f"Fact evidence does not occur in source chunk {chunk.id}."
                )
        return by_ref
