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

    def remove_project(self, project_id: str) -> None:
        project_root = self.project_root(project_id)
        if project_root.exists():
            shutil.rmtree(project_root)
