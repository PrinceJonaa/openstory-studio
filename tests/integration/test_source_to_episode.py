from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi import FastAPI


async def prepare_glass_orchard(
    api_client: httpx.AsyncClient,
    project_id: str,
) -> list[dict[str, Any]]:
    fixture = Path("tests/fixtures/glass_orchard.md")
    imported = await api_client.post(
        f"/projects/{project_id}/sources",
        files={"file": (fixture.name, fixture.read_bytes(), "text/markdown")},
    )
    assert imported.status_code == 201
    extracted = await api_client.post(f"/projects/{project_id}/canon/extract", json={})
    assert extracted.status_code == 200
    return imported.json()["chunks"]


@pytest.mark.asyncio
async def test_source_to_episode_vertical_slice(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    chunks = await prepare_glass_orchard(api_client, project_id)
    request = {
        "source_chunk_ids": [chunk["id"] for chunk in reversed(chunks)],
        "number": 1,
        "target_format": "storyboard",
    }

    response = await api_client.post(
        f"/projects/{project_id}/episodes/adapt",
        json=request,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["job"]["status"] == "succeeded"
    assert payload["job"]["progress_current"] == 1
    episode = payload["result"]["episode"]
    scenes = payload["result"]["scenes"]
    assert episode["title"] == "The Crossing"
    assert episode["source_chunk_ids"] == [chunk["id"] for chunk in chunks]
    assert episode["status"] == "draft"
    assert [scene["ordinal"] for scene in scenes] == list(range(1, len(scenes) + 1))
    assert all(scene["status"] == "draft" for scene in scenes)
    assert scenes[-1]["location_entity_id"] is not None
    assert scenes[-1]["character_entity_ids"]

    listed = await api_client.get(f"/projects/{project_id}/episodes")
    detail = await api_client.get(f"/episodes/{episode['id']}")
    assert listed.json() == [episode]
    assert detail.json() == payload["result"]


@pytest.mark.asyncio
async def test_duplicate_episode_number_is_rejected_and_job_failure_is_visible(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    chunks = await prepare_glass_orchard(api_client, project_id)
    request = {
        "source_chunk_ids": [chunk["id"] for chunk in chunks],
        "number": 1,
        "target_format": "storyboard",
    }
    first = await api_client.post(f"/projects/{project_id}/episodes/adapt", json=request)
    duplicate = await api_client.post(f"/projects/{project_id}/episodes/adapt", json=request)

    assert first.status_code == 200
    assert duplicate.status_code == 409
    jobs = (await api_client.get(f"/projects/{project_id}/jobs")).json()
    assert [job["status"] for job in jobs[-2:]] == ["succeeded", "failed"]


@pytest.mark.asyncio
async def test_episode_and_scene_status_routes_preserve_locked_artifacts(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    chunks = await prepare_glass_orchard(api_client, project_id)
    adapted = await api_client.post(
        f"/projects/{project_id}/episodes/adapt",
        json={
            "source_chunk_ids": [chunk["id"] for chunk in chunks],
            "number": 1,
            "target_format": "storyboard",
        },
    )
    result = adapted.json()["result"]
    episode_id = result["episode"]["id"]
    scene_id = result["scenes"][0]["id"]

    for target in ("review", "approved", "locked"):
        changed = await api_client.patch(
            f"/episodes/{episode_id}/status",
            json={"status": target},
        )
        assert changed.status_code == 200
        assert changed.json()["status"] == target

    rejected = await api_client.patch(
        f"/episodes/{episode_id}/status",
        json={"status": "revise"},
    )
    scene_review = await api_client.patch(
        f"/scenes/{scene_id}/status",
        json={"status": "review"},
    )

    assert rejected.status_code == 409
    assert (await api_client.get(f"/episodes/{episode_id}")).json()["episode"]["status"] == (
        "locked"
    )
    assert scene_review.status_code == 200
    assert scene_review.json()["status"] == "review"


@pytest.mark.asyncio
async def test_adaptation_rejects_source_chunk_from_another_project(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    chunks = await prepare_glass_orchard(api_client, project_id)
    other = await api_client.post(
        "/projects",
        json={"name": "Another Story", "target_format": "storyboard"},
    )
    assert other.status_code == 201

    response = await api_client.post(
        f"/projects/{other.json()['id']}/episodes/adapt",
        json={
            "source_chunk_ids": [chunks[0]["id"]],
            "number": 1,
            "target_format": "storyboard",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_adaptation_prompt_includes_snapshot_and_future_canon_prohibition(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
    api_app: FastAPI,
) -> None:
    from openstory.providers.text.mock import MockTextProvider

    class RecordingProvider(MockTextProvider):
        def __init__(self) -> None:
            super().__init__()
            self.prompts: list[str] = []

        async def generate_structured(self, **kwargs: Any) -> Any:
            self.prompts.append(str(kwargs["user_prompt"]))
            return await super().generate_structured(**kwargs)

    project_id = str(api_project["id"])
    chunks = await prepare_glass_orchard(api_client, project_id)
    provider = RecordingProvider()
    api_app.state.text_provider = provider

    response = await api_client.post(
        f"/projects/{project_id}/episodes/adapt",
        json={
            "source_chunk_ids": [chunk["id"] for chunk in chunks],
            "number": 1,
            "target_format": "storyboard",
        },
    )

    assert response.status_code == 200
    assert len(provider.prompts) == 1
    assert "Canon snapshot at ordinal 2" in provider.prompts[0]
    assert "Do not use future canon" in provider.prompts[0]
    assert "Omissions and reorderings" in provider.prompts[0]
