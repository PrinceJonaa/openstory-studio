from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path

from PIL import Image

from openstory.domain.assets import RenderVersion
from openstory.domain.ids import new_id
from openstory.domain.status import LockedArtifactError, ProductionStatus
from openstory.domain.storyboard import StoryboardPanel
from openstory.persistence.repositories import (
    OpenStoryRepository,
    RenderVersionCollisionError,
)
from openstory.providers.image.base import ImageGenerationProvider
from openstory.services.workspace import WorkspaceManager


class RenderTargetNotFoundError(LookupError):
    pass


class RenderOutputError(ValueError):
    pass


def build_panel_render_prompt(
    panel: StoryboardPanel,
    character_names: Sequence[str],
    location_name: str | None,
) -> str:
    return "\n".join(
        [
            f"PANEL {panel.ordinal}",
            f"SHOT: {panel.shot_type} · {panel.framing}",
            f"CHARACTERS: {', '.join(character_names) if character_names else 'None'}",
            f"LOCATION: {location_name or 'Unspecified'}",
            f"ACTION: {panel.action}",
            f"VISUAL: {panel.visual_description}",
            f"IMAGE PROMPT: {panel.image_prompt}",
        ]
    )


class RenderStoryboardService:
    def __init__(
        self,
        repository: OpenStoryRepository,
        workspace_manager: WorkspaceManager,
        provider: ImageGenerationProvider,
    ) -> None:
        self.repository = repository
        self.workspace_manager = workspace_manager
        self.provider = provider

    async def render_panel(
        self,
        panel_id: str,
        width: int = 768,
        height: int = 1024,
        seed: int | None = None,
    ) -> RenderVersion:
        panel, scene_id, project_id = self._load_panel_context(panel_id)
        if panel.status is ProductionStatus.LOCKED:
            raise LockedArtifactError(panel.status, ProductionStatus.DRAFT)

        entities = self.repository.get_canon_entities_by_ids(
            project_id,
            [
                *panel.character_entity_ids,
                *([panel.location_entity_id] if panel.location_entity_id is not None else []),
            ],
        )
        by_id = {entity.id: entity for entity in entities}
        character_names = [
            by_id[entity_id].canonical_name
            for entity_id in panel.character_entity_ids
            if entity_id in by_id
        ]
        location_name = (
            by_id[panel.location_entity_id].canonical_name
            if panel.location_entity_id in by_id
            else None
        )
        prompt = build_panel_render_prompt(panel, character_names, location_name)

        for attempt in range(2):
            version = self.repository.next_render_version(panel.id)
            output_path = self.workspace_manager.render_path(
                project_id,
                scene_id,
                panel.ordinal,
                version,
            )
            while output_path.exists():
                version += 1
                output_path = self.workspace_manager.render_path(
                    project_id,
                    scene_id,
                    panel.ordinal,
                    version,
                )
            resolved_seed = seed if seed is not None else _deterministic_seed(panel.id, version)
            result = await self.provider.generate(
                prompt=prompt,
                negative_prompt=panel.negative_prompt,
                width=width,
                height=height,
                seed=resolved_seed,
                output_path=output_path,
                references=None,
            )
            self._verify_output(result.output_path, width, height)
            render = RenderVersion(
                id=new_id(),
                panel_id=panel.id,
                version=version,
                output_path=str(result.output_path.resolve()),
                width=result.width,
                height=result.height,
                seed=result.seed,
                provider=result.provider,
                metadata={
                    **result.metadata,
                    "panel_ordinal": panel.ordinal,
                    "scene_id": scene_id,
                    "structured_prompt": prompt,
                },
            )
            try:
                return self.repository.add_render_version(render)
            except RenderVersionCollisionError:
                result.output_path.unlink(missing_ok=True)
                if attempt == 1:
                    raise
        raise RuntimeError("Render version allocation exhausted unexpectedly.")

    async def render_scene(
        self,
        scene_id: str,
        width: int = 768,
        height: int = 1024,
    ) -> list[RenderVersion]:
        scene = self.repository.get_scene(scene_id)
        if scene is None:
            raise RenderTargetNotFoundError("Scene not found.")
        panels = self.repository.list_storyboard_panels(scene_id)
        if not panels:
            raise RenderTargetNotFoundError("Scene has no storyboard panels.")
        locked = [panel for panel in panels if panel.status is ProductionStatus.LOCKED]
        if locked:
            raise LockedArtifactError(ProductionStatus.LOCKED, ProductionStatus.DRAFT)
        renders: list[RenderVersion] = []
        for panel in panels:
            renders.append(
                await self.render_panel(
                    panel.id,
                    width=width,
                    height=height,
                )
            )
        return renders

    def _load_panel_context(self, panel_id: str) -> tuple[StoryboardPanel, str, str]:
        panel = self.repository.get_storyboard_panel(panel_id)
        if panel is None:
            raise RenderTargetNotFoundError("Storyboard panel not found.")
        scene = self.repository.get_scene(panel.scene_id)
        if scene is None:
            raise RenderTargetNotFoundError("Scene not found for storyboard panel.")
        episode = self.repository.get_episode(scene.episode_id)
        if episode is None:
            raise RenderTargetNotFoundError("Episode not found for storyboard panel.")
        return panel, scene.id, episode.project_id

    @staticmethod
    def _verify_output(output_path: Path, width: int, height: int) -> None:
        if not output_path.is_file():
            raise RenderOutputError("Image provider did not create the requested output file.")
        with Image.open(output_path) as image:
            if image.format != "PNG" or image.size != (width, height):
                raise RenderOutputError("Image provider output failed PNG verification.")
            image.verify()


def _deterministic_seed(panel_id: str, version: int) -> int:
    digest = sha256(f"{panel_id}:{version}".encode()).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF
