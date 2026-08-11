from pathlib import Path


def test_project_creation_creates_workspace(tmp_path: Path) -> None:
    from openstory.application.create_project import CreateProjectService
    from openstory.domain.project import ProjectCreate
    from openstory.persistence.db import create_db_engine, init_db, make_session_factory
    from openstory.persistence.repositories import OpenStoryRepository
    from openstory.services.workspace import WorkspaceManager

    engine = create_db_engine(f"sqlite+pysqlite:///{tmp_path / 'openstory.db'}")
    init_db(engine)
    session_factory = make_session_factory(engine)
    workspace_manager = WorkspaceManager(tmp_path / "workspaces")

    with session_factory() as session:
        repository = OpenStoryRepository(session)
        project = CreateProjectService(repository, workspace_manager).execute(
            ProjectCreate(name="The Glass Orchard", target_format="storyboard")
        )

        root = workspace_manager.project_root(project.id)
        assert root.is_dir()
        assert {path.name for path in root.iterdir()} == {
            "source",
            "canon",
            "episodes",
            "assets",
            "renders",
            "exports",
        }
        assert repository.get_project(project.id) == project


def test_project_name_is_normalized_into_unique_slug(tmp_path: Path) -> None:
    from openstory.application.create_project import CreateProjectService
    from openstory.domain.project import ProjectCreate
    from openstory.persistence.db import create_db_engine, init_db, make_session_factory
    from openstory.persistence.repositories import DuplicateProjectSlugError, OpenStoryRepository
    from openstory.services.workspace import WorkspaceManager

    engine = create_db_engine(f"sqlite+pysqlite:///{tmp_path / 'openstory.db'}")
    init_db(engine)
    session_factory = make_session_factory(engine)
    workspace_manager = WorkspaceManager(tmp_path / "workspaces")

    with session_factory() as session:
        service = CreateProjectService(OpenStoryRepository(session), workspace_manager)
        first = service.execute(
            ProjectCreate(name="  The   Glass Orchard  ", target_format="storyboard")
        )
        assert first.name == "The Glass Orchard"
        assert first.slug == "the-glass-orchard"

        try:
            service.execute(ProjectCreate(name="The Glass Orchard", target_format="comic"))
        except DuplicateProjectSlugError:
            pass
        else:
            raise AssertionError("duplicate normalized slug must be rejected")

