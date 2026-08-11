from pathlib import Path

from openstory.domain.adaptation import (
    AdaptEpisodeCommand,
    Episode,
    EpisodeAdaptationResponse,
    EpisodeDetail,
    Scene,
    SceneDraft,
)
from openstory.domain.canon import CanonEntity, EntityKind
from openstory.domain.ids import new_id
from openstory.domain.project import TargetFormat
from openstory.domain.source import SourceChunk
from openstory.persistence.repositories import OpenStoryRepository, normalize_entity_name
from openstory.providers.text.base import TextGenerationProvider

EPISODE_PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "episode_adapt.md"


class AdaptationProjectNotFoundError(LookupError):
    pass


class AdaptationChunkSelectionError(LookupError):
    pass


class AdaptationValidationError(ValueError):
    pass


class AdaptEpisodeService:
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
        source_chunk_ids: list[str],
        number: int,
        target_format: TargetFormat,
    ) -> EpisodeDetail:
        command = AdaptEpisodeCommand(
            project_id=project_id,
            source_chunk_ids=source_chunk_ids,
            number=number,
            target_format=target_format,
        )
        project = self.repository.get_project(project_id)
        if project is None:
            raise AdaptationProjectNotFoundError("Project not found.")
        chunks = self._select_chunks(project_id, command.source_chunk_ids)
        snapshot_ordinal = max(chunk.ordinal for chunk in chunks)
        snapshot = self.repository.get_canon_snapshot(project_id, snapshot_ordinal)
        response = await self.provider.generate_structured(
            system_prompt=EPISODE_PROMPT_PATH.read_text(encoding="utf-8"),
            user_prompt=self._build_user_prompt(
                project.name,
                command.target_format,
                chunks,
                snapshot.model_dump_json(indent=2),
                snapshot_ordinal,
            ),
            schema=EpisodeAdaptationResponse,
        )

        episode = Episode(
            id=new_id(),
            project_id=project_id,
            number=command.number,
            title=response.episode.title,
            source_chunk_ids=[chunk.id for chunk in chunks],
            logline=response.episode.logline,
            adaptation_notes=response.episode.adaptation_notes,
        )
        scenes = [
            self._resolve_scene(episode.id, draft, snapshot.entities)
            for draft in response.scenes
        ]
        persisted_episode, persisted_scenes = self.repository.add_episode(episode, scenes)
        return EpisodeDetail(episode=persisted_episode, scenes=persisted_scenes)

    def _select_chunks(
        self,
        project_id: str,
        source_chunk_ids: list[str],
    ) -> list[SourceChunk]:
        available = self.repository.list_source_chunks(project_id)
        requested = set(source_chunk_ids)
        available_ids = {chunk.id for chunk in available}
        missing = sorted(requested - available_ids)
        if missing:
            raise AdaptationChunkSelectionError(
                f"Source chunks do not belong to this project: {', '.join(missing)}"
            )
        return [chunk for chunk in available if chunk.id in requested]

    @staticmethod
    def _build_user_prompt(
        project_name: str,
        target_format: TargetFormat,
        chunks: list[SourceChunk],
        snapshot_json: str,
        snapshot_ordinal: int,
    ) -> str:
        rendered_chunks = "\n".join(
            (
                f"--- CHUNK {chunk.ordinal}: {chunk.heading or 'Untitled'} ---\n"
                f"{chunk.text}"
            )
            for chunk in chunks
        )
        return (
            f"Project: {project_name}\n"
            f"Target format: {target_format.value}\n"
            f"Canon snapshot at ordinal {snapshot_ordinal}:\n{snapshot_json}\n\n"
            "Do not use future canon beyond this snapshot.\n"
            "Omissions and reorderings must be explicit in adaptation_notes.\n\n"
            f"SOURCE CHUNKS:\n{rendered_chunks}"
        )

    def _resolve_scene(
        self,
        episode_id: str,
        draft: SceneDraft,
        entities: list[CanonEntity],
    ) -> Scene:
        location = (
            self._resolve_entity_ref(draft.location_ref, entities, EntityKind.LOCATION)
            if draft.location_ref is not None
            else None
        )
        characters = [
            self._resolve_entity_ref(reference, entities, EntityKind.CHARACTER)
            for reference in draft.character_refs
        ]
        character_ids = list(dict.fromkeys(entity.id for entity in characters))
        return Scene(
            id=new_id(),
            episode_id=episode_id,
            ordinal=draft.ordinal,
            title=draft.title,
            purpose=draft.purpose,
            location_entity_id=location.id if location is not None else None,
            character_entity_ids=character_ids,
            summary=draft.summary,
        )

    @staticmethod
    def _resolve_entity_ref(
        reference: str,
        entities: list[CanonEntity],
        expected_kind: EntityKind,
    ) -> CanonEntity:
        normalized = normalize_entity_name(reference)
        canonical_matches = [
            entity
            for entity in entities
            if normalize_entity_name(entity.canonical_name) == normalized
        ]
        matches = canonical_matches or [
            entity
            for entity in entities
            if normalized in {normalize_entity_name(alias) for alias in entity.aliases}
        ]
        if len(matches) != 1:
            raise AdaptationValidationError(
                f"Entity reference '{reference}' does not resolve uniquely in the canon snapshot."
            )
        entity = matches[0]
        if entity.kind is not expected_kind:
            raise AdaptationValidationError(
                f"Entity reference '{reference}' is {entity.kind.value}, not {expected_kind.value}."
            )
        return entity
