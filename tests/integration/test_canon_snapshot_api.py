from pathlib import Path

import httpx
import pytest


@pytest.mark.asyncio
async def test_canon_snapshot_api_returns_only_referenced_entities(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    fixture = Path("tests/fixtures/glass_orchard.md")
    imported = await api_client.post(
        f"/projects/{project_id}/sources",
        files={"file": (fixture.name, fixture.read_bytes(), "text/markdown")},
    )
    assert imported.status_code == 201
    extracted = await api_client.post(f"/projects/{project_id}/canon/extract", json={})
    assert extracted.status_code == 200

    response = await api_client.get(
        f"/projects/{project_id}/canon/snapshot",
        params={"ordinal": 1},
    )

    assert response.status_code == 200
    snapshot = response.json()
    referenced_ids = {
        entity_id
        for fact in snapshot["facts"]
        for entity_id in (fact["subject_entity_id"], fact["object_entity_id"])
        if entity_id is not None
    }
    assert {entity["id"] for entity in snapshot["entities"]} == referenced_ids


@pytest.mark.asyncio
async def test_canon_snapshot_api_returns_empty_snapshot_without_active_facts(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])

    response = await api_client.get(
        f"/projects/{project_id}/canon/snapshot",
        params={"ordinal": 0},
    )

    assert response.status_code == 200
    assert response.json() == {
        "project_id": project_id,
        "ordinal": 0,
        "entities": [],
        "facts": [],
    }


@pytest.mark.asyncio
async def test_canon_snapshot_api_validates_project_and_ordinal(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])

    missing = await api_client.get(
        "/projects/missing/canon/snapshot",
        params={"ordinal": 1},
    )
    negative = await api_client.get(
        f"/projects/{project_id}/canon/snapshot",
        params={"ordinal": -1},
    )

    assert missing.status_code == 404
    assert negative.status_code == 422
