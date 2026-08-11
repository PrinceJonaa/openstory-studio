from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from openstory_api.dependencies import Settings
from openstory_api.main import create_app


@pytest.fixture
def api_app(tmp_path: Path) -> FastAPI:
    settings = Settings(
        database_url=f"sqlite+pysqlite:///{tmp_path / 'api.db'}",
        workspace_root=tmp_path / "workspaces",
        cors_origins=["http://localhost:5173"],
    )
    return create_app(settings)


@pytest_asyncio.fixture
async def api_client(api_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with api_app.router.lifespan_context(api_app), httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def api_project(api_client: httpx.AsyncClient) -> dict[str, object]:
    response = await api_client.post(
        "/projects",
        json={"name": "The Glass Orchard", "target_format": "storyboard"},
    )
    assert response.status_code == 201
    return response.json()
