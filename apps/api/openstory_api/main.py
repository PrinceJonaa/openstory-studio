from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openstory.persistence.db import create_db_engine, init_db, make_session_factory
from openstory.services.workspace import WorkspaceManager

from openstory_api.dependencies import Settings
from openstory_api.routes import health, projects


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings()
    engine = create_db_engine(resolved_settings.database_url)
    session_factory = make_session_factory(engine)
    workspace_manager = WorkspaceManager(resolved_settings.workspace_root)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        init_db(engine)
        workspace_manager.root.mkdir(parents=True, exist_ok=True)
        yield
        engine.dispose()

    application = FastAPI(title="OpenStory Studio API", lifespan=lifespan)
    application.state.session_factory = session_factory
    application.state.workspace_manager = workspace_manager
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health.router)
    application.include_router(projects.router)
    return application


app = create_app()

