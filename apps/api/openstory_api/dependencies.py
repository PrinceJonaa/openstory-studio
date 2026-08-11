from collections.abc import Generator
from pathlib import Path
from typing import Annotated, cast

import httpx
from fastapi import Depends, Request
from openstory.persistence.repositories import OpenStoryRepository
from openstory.providers.text.base import TextGenerationProvider
from openstory.providers.text.mock import MockTextProvider
from openstory.providers.text.openai_compatible import OpenAICompatibleTextProvider
from openstory.services.workspace import WorkspaceManager
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.orm import Session


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPENSTORY_", extra="ignore")

    database_url: str = "sqlite+pysqlite:///./openstory.db"
    workspace_root: Path = Path("./workspaces")
    text_provider: str = "mock"
    text_base_url: str = "http://127.0.0.1:8080/v1"
    text_api_key: str = "local"
    text_model: str = "local-model"
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


class TextProviderConfigurationError(ValueError):
    pass


def build_text_provider(settings: Settings) -> TextGenerationProvider:
    if settings.text_provider == "mock":
        return MockTextProvider()
    if settings.text_provider == "openai_compatible":
        return OpenAICompatibleTextProvider(
            client=httpx.AsyncClient(timeout=120.0),
            base_url=settings.text_base_url,
            api_key=settings.text_api_key,
            model=settings.text_model,
        )
    raise TextProviderConfigurationError(
        f"Unknown text provider '{settings.text_provider}'. "
        "Expected 'mock' or 'openai_compatible'."
    )


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
