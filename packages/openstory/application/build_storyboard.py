from pathlib import Path

from openstory.domain.adaptation import Episode, Scene
from openstory.domain.canon import CanonEntity, EntityKind
from openstory.domain.ids import new_id
from openstory.domain.storyboard import (
    DialogueLine,
    DialogueLineDraft,
    PanelDraft,
    StoryboardBuildResponse,
    StoryboardPanel,
)
from openstory.persistence.repositories import (
    OpenStoryRepository,
    StoryboardReplacementError,
    normalize_entity_name,
)
from openstory.providers.text.base import TextGenerationProvider

STORYBOARD_PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "storyboard_build.md"


class StoryboardSceneNotFoundError(LookupError):
    pass


class StoryboardValidationError(ValueError):
    pass


class BuildStoryboardService:
    def __init__(
        self,
        repository: OpenStoryRepository,
        provider: TextGenerationProvider,
    ) -> None:
        self.repository = repository
        self.provider = provider

    async def execute(self, scene_id: str) -> list[StoryboardPanel]:
        scene = self.repository.get_scene(scene_id)
        if scene is None:
            raise StoryboardSceneNotFoundError("Scene not found.")
        episode = self.repository.get_episode(scene.episode_id)
        if episode is None:
            raise StoryboardSceneNotFoundError("Episode not found for scene.")
        existing = self.repository.list_storyboard_panels(scene_id)
        if any(panel.status.value != "draft" for panel in existing):
            raise StoryboardReplacementError(
                "Storyboard replacement requires every existing panel to be in draft status."
            )

        chunks = [
            chunk
            for chunk in self.repository.list_source_chunks(episode.project_id)
            if chunk.id in set(episode.source_chunk_ids)
        ]
        if not chunks:
            raise StoryboardValidationError("Episode has no available source chunks.")
        snapshot_ordinal = max(chunk.ordinal for chunk in chunks)
        snapshot = self.repository.get_canon_snapshot(episode.project_id, snapshot_ordinal)
        response = await self.provider.generate_structured(
            system_prompt=STORYBOARD_PROMPT_PATH.read_text(encoding="utf-8"),
            user_prompt=self._build_user_prompt(
                scene,
                episode,
                snapshot.model_dump_json(indent=2),
                snapshot_ordinal,
            ),
            schema=StoryboardBuildResponse,
        )
        panels = [
            self._resolve_panel(scene, draft, snapshot.entities)
            for draft in response.panels
        ]
        return self.repository.replace_draft_storyboard(scene_id, panels)

    @staticmethod
    def _build_user_prompt(
        scene: Scene,
        episode: Episode,
        snapshot_json: str,
        snapshot_ordinal: int,
    ) -> str:
        return (
            f"Scene title: {scene.title}\n"
            f"Scene summary: {scene.summary}\n"
            f"Scene JSON:\n{scene.model_dump_json(indent=2)}\n\n"
            f"Episode adaptation context:\n{episode.model_dump_json(indent=2)}\n\n"
            f"Canon snapshot at ordinal {snapshot_ordinal}:\n{snapshot_json}\n\n"
            "Create 6-12 visual beats by default. Do not invent future canon."
        )

    def _resolve_panel(
        self,
        scene: Scene,
        draft: PanelDraft,
        entities: list[CanonEntity],
    ) -> StoryboardPanel:
        location = (
            self._resolve_entity_ref(draft.location_ref, entities, EntityKind.LOCATION)
            if draft.location_ref is not None
            else None
        )
        if location is not None and location.id != scene.location_entity_id:
            raise StoryboardValidationError(
                f"Panel location '{location.canonical_name}' does not match its scene."
            )

        characters = [
            self._resolve_entity_ref(reference, entities, EntityKind.CHARACTER)
            for reference in draft.character_refs
        ]
        character_ids = list(dict.fromkeys(entity.id for entity in characters))
        invalid_character_ids = set(character_ids) - set(scene.character_entity_ids)
        if invalid_character_ids:
            raise StoryboardValidationError(
                "Panel references characters that are not present in the scene."
            )

        dialogue = [
            self._resolve_dialogue_line(line, entities, scene)
            for line in draft.dialogue
        ]
        for line in dialogue:
            if line.speaker_entity_id is not None and line.speaker_entity_id not in character_ids:
                character_ids.append(line.speaker_entity_id)

        return StoryboardPanel(
            id=new_id(),
            scene_id=scene.id,
            ordinal=draft.ordinal,
            shot_type=draft.shot_type,
            framing=draft.framing,
            action=draft.action,
            visual_description=draft.visual_description,
            dialogue=dialogue,
            character_entity_ids=character_ids,
            location_entity_id=location.id if location is not None else None,
            referenced_asset_ids=[],
            image_prompt=draft.image_prompt,
            negative_prompt=draft.negative_prompt,
        )

    def _resolve_dialogue_line(
        self,
        draft: DialogueLineDraft,
        entities: list[CanonEntity],
        scene: Scene,
    ) -> DialogueLine:
        speaker = (
            self._resolve_entity_ref(draft.speaker_ref, entities, EntityKind.CHARACTER)
            if draft.speaker_ref is not None
            else None
        )
        if speaker is not None and speaker.id not in scene.character_entity_ids:
            raise StoryboardValidationError(
                f"Dialogue speaker '{speaker.canonical_name}' is not present in the scene."
            )
        return DialogueLine(
            speaker_entity_id=speaker.id if speaker is not None else None,
            speaker_name=draft.speaker_name,
            text=draft.text,
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
            raise StoryboardValidationError(
                f"Entity reference '{reference}' does not resolve uniquely in the canon snapshot."
            )
        entity = matches[0]
        if entity.kind is not expected_kind:
            raise StoryboardValidationError(
                f"Entity reference '{reference}' is {entity.kind.value}, not {expected_kind.value}."
            )
        return entity
