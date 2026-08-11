from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest


@asynccontextmanager
async def make_client(tmp_path: Path) -> AsyncIterator[httpx.AsyncClient]:
    from openstory_api.dependencies import Settings
    from openstory_api.main import create_app

    settings = Settings(
        database_url=f"sqlite+pysqlite:///{tmp_path / 'api.db'}",
        workspace_root=tmp_path / "workspaces",
        cors_origins=["http://localhost:5173"],
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app), httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_health_returns_ok(tmp_path: Path) -> None:
    async with make_client(tmp_path) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_project_api_creates_lists_and_fetches_project(tmp_path: Path) -> None:
    async with make_client(tmp_path) as client:
        created = await client.post(
            "/projects",
            json={"name": "The Glass Orchard", "target_format": "storyboard"},
        )
        assert created.status_code == 201
        project = created.json()

        listed = await client.get("/projects")
        fetched = await client.get(f"/projects/{project['id']}")

    assert [item["id"] for item in listed.json()] == [project["id"]]
    assert fetched.json() == project


@pytest.mark.asyncio
async def test_project_api_reports_duplicate_and_missing_project(tmp_path: Path) -> None:
    async with make_client(tmp_path) as client:
        payload = {"name": "The Glass Orchard", "target_format": "storyboard"}
        assert (await client.post("/projects", json=payload)).status_code == 201
        duplicate = await client.post("/projects", json=payload)
        missing = await client.get("/projects/missing")

    assert duplicate.status_code == 409
    assert missing.status_code == 404
