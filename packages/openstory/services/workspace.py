import shutil
from pathlib import Path

PROJECT_DIRECTORIES = ("source", "canon", "episodes", "assets", "renders", "exports")


class UnsafeWorkspacePathError(ValueError):
    pass


class WorkspaceManager:
    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()

    def project_root(self, project_id: str) -> Path:
        candidate = (self.root / project_id).resolve()
        if not candidate.is_relative_to(self.root):
            raise UnsafeWorkspacePathError("Project path escapes the workspace root.")
        return candidate

    def create_project(self, project_id: str) -> Path:
        project_root = self.project_root(project_id)
        project_root.mkdir(parents=True, exist_ok=False)
        for directory in PROJECT_DIRECTORIES:
            (project_root / directory).mkdir()
        return project_root

    def source_path(self, project_id: str, filename: str) -> Path:
        source_root = (self.project_root(project_id) / "source").resolve()
        candidate = (source_root / Path(filename).name).resolve()
        if not candidate.is_relative_to(source_root):
            raise UnsafeWorkspacePathError("Source path escapes the project source directory.")
        return candidate

    def render_path(
        self,
        project_id: str,
        scene_id: str,
        panel_ordinal: int,
        version: int,
    ) -> Path:
        render_root = (self.project_root(project_id) / "renders").resolve()
        candidate = (
            render_root
            / scene_id
            / f"panel-{panel_ordinal:04d}"
            / f"v{version:03d}.png"
        ).resolve()
        if not candidate.is_relative_to(render_root):
            raise UnsafeWorkspacePathError("Render path escapes the project render directory.")
        return candidate

    def episode_export_root(self, project_id: str, episode_id: str) -> Path:
        export_root = (self.project_root(project_id) / "exports").resolve()
        candidate = (export_root / episode_id).resolve()
        if not candidate.is_relative_to(export_root):
            raise UnsafeWorkspacePathError("Episode export path escapes the exports directory.")
        return candidate

    def resolve_project_file(self, project_id: str, persisted_path: str) -> Path:
        project_root = self.project_root(project_id)
        candidate = Path(persisted_path).expanduser().resolve()
        if not candidate.is_relative_to(project_root):
            raise UnsafeWorkspacePathError("Persisted file path escapes the project workspace.")
        return candidate

    def remove_project(self, project_id: str) -> None:
        project_root = self.project_root(project_id)
        if project_root.exists():
            shutil.rmtree(project_root)
