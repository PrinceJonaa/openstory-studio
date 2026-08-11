import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field

from openstory.domain.adaptation import Episode, Scene
from openstory.domain.assets import RenderVersion
from openstory.domain.canon import CanonSnapshot
from openstory.domain.project import Project, utc_now
from openstory.domain.source import SourceChunk, SourceDocument
from openstory.domain.storyboard import StoryboardPanel
from openstory.persistence.repositories import OpenStoryRepository
from openstory.services.workspace import WorkspaceManager


class ExportNotFoundError(LookupError):
    pass


class ExportMissingRenderError(ValueError):
    pass


class ExportValidationError(ValueError):
    pass


class ExportManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: int = Field(ge=1)
    episode_id: str = Field(min_length=1)
    created_at: datetime
    source_hashes: list[str]
    render_version_ids: list[str]
    files: list[str]


class ExportBundle(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    project: Project
    source_documents: list[SourceDocument]
    source_chunks: list[SourceChunk]
    canon_snapshot: CanonSnapshot
    episode: Episode
    scenes: list[Scene]
    panels: list[StoryboardPanel]
    renders: list[RenderVersion]


class ExportResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: int = Field(ge=1)
    output_path: str = Field(min_length=1)
    manifest: ExportManifest


class ExportEpisodeService:
    def __init__(
        self,
        repository: OpenStoryRepository,
        workspace_manager: WorkspaceManager,
    ) -> None:
        self.repository = repository
        self.workspace_manager = workspace_manager

    def execute(self, project_id: str, episode_id: str) -> ExportResult:
        bundle, source_render_pairs = self._build_bundle(project_id, episode_id)
        episode_root = self.workspace_manager.episode_export_root(project_id, episode_id)
        episode_root.mkdir(parents=True, exist_ok=True)
        version = _next_export_version(episode_root)
        temporary_root = episode_root / f".v{version:03d}.tmp"
        output_root = episode_root / f"v{version:03d}"
        while temporary_root.exists() or output_root.exists():
            version += 1
            temporary_root = episode_root / f".v{version:03d}.tmp"
            output_root = episode_root / f"v{version:03d}"

        temporary_root.mkdir(parents=False, exist_ok=False)
        try:
            storyboard_root = temporary_root / "storyboard"
            storyboard_root.mkdir()
            image_files: list[str] = []
            for export_ordinal, (_render, source_path) in enumerate(
                source_render_pairs,
                start=1,
            ):
                relative_path = f"storyboard/panel-{export_ordinal:04d}.png"
                shutil.copy2(source_path, temporary_root / relative_path)
                image_files.append(relative_path)

            _write_json(temporary_root / "episode.json", bundle.model_dump(mode="json"))
            (temporary_root / "episode.md").write_text(
                _build_markdown(bundle),
                encoding="utf-8",
            )
            files = ["episode.json", "episode.md", "manifest.json", *image_files]
            manifest = ExportManifest(
                version=version,
                episode_id=episode_id,
                created_at=utc_now(),
                source_hashes=[document.sha256 for document in bundle.source_documents],
                render_version_ids=[render.id for render in bundle.renders],
                files=files,
            )
            _write_json(
                temporary_root / "manifest.json",
                manifest.model_dump(mode="json"),
            )
            missing_files = [
                relative_path
                for relative_path in manifest.files
                if not (temporary_root / relative_path).is_file()
            ]
            if missing_files:
                raise ExportValidationError(
                    f"Export verification failed for: {', '.join(missing_files)}"
                )
            if output_root.exists():
                raise ExportValidationError("Export version already exists.")
            os.replace(temporary_root, output_root)
        except Exception:
            if temporary_root.exists():
                shutil.rmtree(temporary_root)
            raise

        return ExportResult(
            version=version,
            output_path=str(output_root.resolve()),
            manifest=manifest,
        )

    def _build_bundle(
        self,
        project_id: str,
        episode_id: str,
    ) -> tuple[ExportBundle, list[tuple[RenderVersion, Path]]]:
        project = self.repository.get_project(project_id)
        episode = self.repository.get_episode(episode_id)
        if project is None or episode is None or episode.project_id != project_id:
            raise ExportNotFoundError("Episode not found in this project.")

        requested_chunk_ids = set(episode.source_chunk_ids)
        source_chunks = [
            chunk
            for chunk in self.repository.list_source_chunks(project_id)
            if chunk.id in requested_chunk_ids
        ]
        if len(source_chunks) != len(requested_chunk_ids):
            raise ExportValidationError("Episode source chunks are incomplete.")
        document_ids = {chunk.document_id for chunk in source_chunks}
        source_documents = [
            document
            for document in self.repository.list_source_documents(project_id)
            if document.id in document_ids
        ]
        if len(source_documents) != len(document_ids):
            raise ExportValidationError("Episode source documents are incomplete.")

        snapshot_ordinal = max(chunk.ordinal for chunk in source_chunks)
        canon_snapshot = self.repository.get_canon_snapshot(project_id, snapshot_ordinal)
        scenes = self.repository.list_scenes(episode_id)
        panels = [
            panel
            for scene in scenes
            for panel in self.repository.list_storyboard_panels(scene.id)
        ]
        if not panels:
            raise ExportMissingRenderError("Episode has no storyboard panels to export.")

        renders: list[RenderVersion] = []
        source_render_pairs: list[tuple[RenderVersion, Path]] = []
        scene_by_id = {scene.id: scene for scene in scenes}
        for panel in panels:
            render = self.repository.select_export_render(panel.id)
            if render is None:
                scene = scene_by_id[panel.scene_id]
                raise ExportMissingRenderError(
                    f"Panel {panel.ordinal} in Scene {scene.ordinal} has no available render."
                )
            source_path = self.workspace_manager.resolve_project_file(
                project_id,
                render.output_path,
            )
            _verify_png(source_path, render.width, render.height)
            renders.append(render)
            source_render_pairs.append((render, source_path))

        return (
            ExportBundle(
                project=project,
                source_documents=source_documents,
                source_chunks=source_chunks,
                canon_snapshot=canon_snapshot,
                episode=episode,
                scenes=scenes,
                panels=panels,
                renders=renders,
            ),
            source_render_pairs,
        )


def _next_export_version(episode_root: Path) -> int:
    versions: list[int] = []
    for candidate in episode_root.iterdir():
        match = re.fullmatch(r"\.?v(\d+)\.tmp|v(\d+)", candidate.name)
        if match is not None:
            versions.append(int(match.group(1) or match.group(2)))
    return max(versions, default=0) + 1


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _verify_png(path: Path, width: int, height: int) -> None:
    try:
        with Image.open(path) as image:
            image_format = image.format
            image_size = image.size
            image.verify()
    except (OSError, UnidentifiedImageError) as error:
        raise ExportValidationError(f"Render is not a readable PNG: {path.name}") from error
    if image_format != "PNG" or image_size != (width, height):
        raise ExportValidationError(f"Render dimensions do not match metadata: {path.name}")


def _build_markdown(bundle: ExportBundle) -> str:
    panel_export_ordinals = {
        panel.id: ordinal for ordinal, panel in enumerate(bundle.panels, start=1)
    }
    render_by_panel = {render.panel_id: render for render in bundle.renders}
    lines = [
        f"# Episode {bundle.episode.number}: {bundle.episode.title}",
        "",
        f"**Project:** {bundle.project.name}",
        f"**Status:** {bundle.episode.status.value}",
        f"**Logline:** {bundle.episode.logline}",
        "",
        "## Adaptation notes",
        "",
        bundle.episode.adaptation_notes,
        "",
    ]
    for scene in bundle.scenes:
        lines.extend(
            [
                f"## Scene {scene.ordinal}: {scene.title}",
                "",
                f"**Purpose:** {scene.purpose}",
                f"**Status:** {scene.status.value}",
                "",
                scene.summary,
                "",
            ]
        )
        for panel in (panel for panel in bundle.panels if panel.scene_id == scene.id):
            export_ordinal = panel_export_ordinals[panel.id]
            render = render_by_panel[panel.id]
            dialogue = (
                "; ".join(
                    f"{line.speaker_name}: {line.text}" for line in panel.dialogue
                )
                or "—"
            )
            lines.extend(
                [
                    f"### Panel {panel.ordinal}",
                    "",
                    f"![Panel {panel.ordinal}](storyboard/panel-{export_ordinal:04d}.png)",
                    "",
                    f"- **Shot:** {panel.shot_type} — {panel.framing}",
                    f"- **Action:** {panel.action}",
                    f"- **Visual:** {panel.visual_description}",
                    f"- **Dialogue:** {dialogue}",
                    f"- **Panel status:** {panel.status.value}",
                    f"- **Render:** v{render.version:03d} · {render.status.value}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"
