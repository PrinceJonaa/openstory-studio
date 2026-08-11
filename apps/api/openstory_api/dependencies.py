from collections.abc import Generator
from pathlib import Path
from typing import Annotated, cast

from fastapi import Depends, Request
from openstory.persistence.repositories import OpenStoryRepository
from openstory.providers.text.base import TextGenerationProvider
from openstory.services.workspace import WorkspaceManager
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.orm import Session


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPENSTORY_", extra="ignore")

    database_url: str = "sqlite+pysqlite:///./openstory.db"
    workspace_root: Path = Path("./workspaces")
    cors_origins: list[str] = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


def get_session(request: Request) -> Generator[Session, None, None]:
    with request.app.state.session_factory() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_session)]


def get_repository(session: SessionDependency) -> OpenStoryRepository:
    return OpenStoryRepository(session)


def get_workspace_manager(request: Request) -> WorkspaceManager:
    return cast(WorkspaceManager, request.app.state.workspace_manager)


def get_text_provider(request: Request) -> TextGenerationProvider:
    return cast(TextGenerationProvider, request.app.state.text_provider)


RepositoryDependency = Annotated[OpenStoryRepository, Depends(get_repository)]
WorkspaceDependency = Annotated[WorkspaceManager, Depends(get_workspace_manager)]
TextProviderDependency = Annotated[TextGenerationProvider, Depends(get_text_provider)]
