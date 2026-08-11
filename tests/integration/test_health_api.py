import httpx
import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_project_api_creates_lists_and_fetches_project(
    api_client: httpx.AsyncClient,
) -> None:
    created = await api_client.post(
        "/projects",
        json={"name": "The Glass Orchard", "target_format": "storyboard"},
    )
    assert created.status_code == 201
    project = created.json()

    listed = await api_client.get("/projects")
    fetched = await api_client.get(f"/projects/{project['id']}")

    assert [item["id"] for item in listed.json()] == [project["id"]]
    assert fetched.json() == project


@pytest.mark.asyncio
async def test_project_api_reports_duplicate_and_missing_project(
    api_client: httpx.AsyncClient,
) -> None:
    payload = {"name": "The Glass Orchard", "target_format": "storyboard"}
    assert (await api_client.post("/projects", json=payload)).status_code == 201
    duplicate = await api_client.post("/projects", json=payload)
    missing = await api_client.get("/projects/missing")

    assert duplicate.status_code == 409
    assert missing.status_code == 404
