from pathlib import Path
from typing import Any

import httpx
import pytest


async def prepare_crossing_scene(
    api_client: httpx.AsyncClient,
    project_id: str,
) -> dict[str, Any]:
    fixture = Path("tests/fixtures/glass_orchard.md")
    imported = await api_client.post(
        f"/projects/{project_id}/sources",
        files={"file": (fixture.name, fixture.read_bytes(), "text/markdown")},
    )
    assert imported.status_code == 201
    chunks = imported.json()["chunks"]
    assert (
        await api_client.post(f"/projects/{project_id}/canon/extract", json={})
    ).status_code == 200
    adapted = await api_client.post(
        f"/projects/{project_id}/episodes/adapt",
        json={
            "source_chunk_ids": [chunk["id"] for chunk in chunks],
            "number": 1,
            "target_format": "storyboard",
        },
    )
    assert adapted.status_code == 200
    return adapted.json()["result"]["scenes"][-1]


@pytest.mark.asyncio
async def test_episode_to_storyboard_vertical_slice(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    scene = await prepare_crossing_scene(api_client, project_id)

    response = await api_client.post(f"/scenes/{scene['id']}/storyboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["job"]["status"] == "succeeded"
    panels = payload["result"]
    assert len(panels) == 6
    assert [panel["ordinal"] for panel in panels] == list(range(1, 7))
    assert panels[0]["shot_type"] == "wide"
    assert panels[0]["location_entity_id"] == scene["location_entity_id"]
    assert all(panel["status"] == "draft" for panel in panels)
    assert all(panel["render_status"] == "unrendered" for panel in panels)
    assert all(panel["action"] and panel["visual_description"] for panel in panels)
    assert all(panel["image_prompt"] for panel in panels)
    assert any(panel["dialogue"] for panel in panels)

    listed = await api_client.get(f"/scenes/{scene['id']}/storyboard")
    assert listed.json() == panels


@pytest.mark.asyncio
async def test_rebuilding_replaces_an_all_draft_storyboard(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    scene = await prepare_crossing_scene(api_client, project_id)
    first = await api_client.post(f"/scenes/{scene['id']}/storyboard")
    second = await api_client.post(f"/scenes/{scene['id']}/storyboard")

    assert first.status_code == 200
    assert second.status_code == 200
    first_ids = {panel["id"] for panel in first.json()["result"]}
    second_panels = second.json()["result"]
    assert not first_ids & {panel["id"] for panel in second_panels}
    assert (await api_client.get(f"/scenes/{scene['id']}/storyboard")).json() == (
        second_panels
    )


@pytest.mark.asyncio
async def test_rebuilding_cannot_replace_reviewed_or_approved_panels(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    scene = await prepare_crossing_scene(api_client, project_id)
    built = await api_client.post(f"/scenes/{scene['id']}/storyboard")
    panels = built.json()["result"]
    panel_id = panels[0]["id"]
    reviewed = await api_client.patch(
        f"/panels/{panel_id}/status",
        json={"status": "review"},
    )
    assert reviewed.status_code == 200

    rejected = await api_client.post(f"/scenes/{scene['id']}/storyboard")

    assert rejected.status_code == 409
    unchanged = await api_client.get(f"/scenes/{scene['id']}/storyboard")
    assert unchanged.json()[0]["status"] == "review"
    jobs = (await api_client.get(f"/projects/{project_id}/jobs")).json()
    assert jobs[-1]["status"] == "failed"


@pytest.mark.asyncio
async def test_panel_status_route_can_approve_and_lock_without_overwriting(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    scene = await prepare_crossing_scene(api_client, project_id)
    built = await api_client.post(f"/scenes/{scene['id']}/storyboard")
    panel_id = built.json()["result"][0]["id"]

    for target in ("review", "approved", "locked"):
        response = await api_client.patch(
            f"/panels/{panel_id}/status",
            json={"status": target},
        )
        assert response.status_code == 200
        assert response.json()["status"] == target

    rejected = await api_client.patch(
        f"/panels/{panel_id}/status",
        json={"status": "revise"},
    )
    assert rejected.status_code == 409
    assert (await api_client.get(f"/scenes/{scene['id']}/storyboard")).json()[0][
        "status"
    ] == "locked"
