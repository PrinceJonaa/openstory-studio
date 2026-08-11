from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from openstory.providers.image.base import ImageProviderUnavailableError
from PIL import Image


class UnavailableImageProvider:
    async def generate(self, **_kwargs: object) -> None:
        raise ImageProviderUnavailableError("Configured image provider is unavailable.")


async def prepare_storyboard(
    api_client: httpx.AsyncClient,
    project_id: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fixture = Path("tests/fixtures/glass_orchard.md")
    imported = await api_client.post(
        f"/projects/{project_id}/sources",
        files={"file": (fixture.name, fixture.read_bytes(), "text/markdown")},
    )
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
    scene = adapted.json()["result"]["scenes"][-1]
    built = await api_client.post(f"/scenes/{scene['id']}/storyboard")
    assert built.status_code == 200
    return scene, built.json()["result"]


@pytest.mark.asyncio
async def test_panel_render_api_creates_versioned_png_and_serves_it(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    scene, panels = await prepare_storyboard(api_client, project_id)
    panel = panels[0]

    first = await api_client.post(
        f"/panels/{panel['id']}/render",
        json={"width": 480, "height": 640, "seed": 17},
    )
    second = await api_client.post(
        f"/panels/{panel['id']}/render",
        json={"width": 480, "height": 640, "seed": 18},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    first_render = first.json()["result"]
    second_render = second.json()["result"]
    assert first_render["version"] == 1
    assert second_render["version"] == 2
    assert first_render["output_path"] != second_render["output_path"]
    assert first_render["metadata"]["panel_ordinal"] == 1
    listed_renders = await api_client.get(f"/panels/{panel['id']}/renders")
    assert listed_renders.status_code == 200
    assert listed_renders.json() == [first_render, second_render]
    file_response = await api_client.get(f"/renders/{first_render['id']}/file")
    assert file_response.status_code == 200
    assert file_response.headers["content-type"] == "image/png"
    with Image.open(BytesIO(file_response.content)) as image:
        assert image.size == (480, 640)

    restored_panels = (await api_client.get(f"/scenes/{scene['id']}/storyboard")).json()
    assert restored_panels[0]["render_status"] == "rendered"


@pytest.mark.asyncio
async def test_scene_render_reports_panel_count_progress(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    scene, panels = await prepare_storyboard(api_client, project_id)

    response = await api_client.post(
        f"/scenes/{scene['id']}/render",
        json={"width": 320, "height": 480},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["result"]) == len(panels) == 6
    assert payload["job"]["progress_total"] == 6
    assert payload["job"]["progress_current"] == 6
    assert all(Path(render["output_path"]).exists() for render in payload["result"])


@pytest.mark.asyncio
async def test_render_status_changes_do_not_modify_png_bytes(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    _scene, panels = await prepare_storyboard(api_client, project_id)
    rendered = await api_client.post(f"/panels/{panels[0]['id']}/render", json={})
    render = rendered.json()["result"]
    before = (await api_client.get(f"/renders/{render['id']}/file")).content

    for target in ("review", "approved", "locked"):
        changed = await api_client.patch(
            f"/renders/{render['id']}/status",
            json={"status": target},
        )
        assert changed.status_code == 200
        assert changed.json()["status"] == target

    after = (await api_client.get(f"/renders/{render['id']}/file")).content
    assert after == before


@pytest.mark.asyncio
async def test_locked_panel_render_is_rejected_without_new_file(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    _scene, panels = await prepare_storyboard(api_client, project_id)
    panel_id = panels[0]["id"]
    for target in ("review", "approved", "locked"):
        assert (
            await api_client.patch(
                f"/panels/{panel_id}/status",
                json={"status": target},
            )
        ).status_code == 200

    response = await api_client.post(f"/panels/{panel_id}/render", json={})

    assert response.status_code == 409
    jobs = (await api_client.get(f"/projects/{project_id}/jobs")).json()
    assert jobs[-1]["status"] == "failed"


@pytest.mark.asyncio
async def test_unavailable_image_provider_returns_503_and_records_failed_job(
    api_client: httpx.AsyncClient,
    api_app: FastAPI,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    _scene, panels = await prepare_storyboard(api_client, project_id)
    api_app.state.image_provider = UnavailableImageProvider()

    response = await api_client.post(f"/panels/{panels[0]['id']}/render", json={})

    assert response.status_code == 503
    assert response.json()["detail"] == "Configured image provider is unavailable."
    jobs = (await api_client.get(f"/projects/{project_id}/jobs")).json()
    assert jobs[-1]["status"] == "failed"
    assert jobs[-1]["error"] == "Configured image provider is unavailable."
