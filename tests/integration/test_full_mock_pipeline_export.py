from pathlib import Path
from typing import Any

import httpx
import pytest
from openstory.application.export_episode import ExportBundle, ExportManifest
from PIL import Image


async def build_mock_episode(
    api_client: httpx.AsyncClient,
    project_id: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
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
    snapshot = await api_client.get(
        f"/projects/{project_id}/canon/snapshot",
        params={"ordinal": chunks[-1]["ordinal"]},
    )
    assert snapshot.status_code == 200
    adapted = await api_client.post(
        f"/projects/{project_id}/episodes/adapt",
        json={
            "source_chunk_ids": [chunk["id"] for chunk in chunks],
            "number": 1,
            "target_format": "storyboard",
        },
    )
    assert adapted.status_code == 200
    episode = adapted.json()["result"]["episode"]
    scene = adapted.json()["result"]["scenes"][-1]
    storyboard = await api_client.post(f"/scenes/{scene['id']}/storyboard")
    assert storyboard.status_code == 200
    panels = storyboard.json()["result"]
    rendered = await api_client.post(
        f"/scenes/{scene['id']}/render",
        json={"width": 320, "height": 480},
    )
    assert rendered.status_code == 200
    return episode, panels, snapshot.json()["facts"]


@pytest.mark.asyncio
async def test_full_mock_pipeline_export(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    episode, panels, snapshot_facts = await build_mock_episode(api_client, project_id)

    response = await api_client.post(
        f"/projects/{project_id}/export",
        json={"episode_id": episode["id"]},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["job"]["kind"] == "export"
    assert payload["job"]["status"] == "succeeded"
    assert payload["job"]["progress_current"] == len(panels) == 6
    export_root = Path(payload["result"]["output_path"])
    assert (export_root / "episode.json").is_file()
    assert (export_root / "episode.md").is_file()
    assert (export_root / "manifest.json").is_file()
    exported_images = sorted((export_root / "storyboard").glob("panel-*.png"))
    assert len(exported_images) == 6

    bundle = ExportBundle.model_validate_json(
        (export_root / "episode.json").read_text(encoding="utf-8")
    )
    manifest = ExportManifest.model_validate_json(
        (export_root / "manifest.json").read_text(encoding="utf-8")
    )
    assert bundle.episode.id == episode["id"]
    assert bundle.canon_snapshot.facts
    assert {fact.source_chunk_id for fact in bundle.canon_snapshot.facts} == {
        fact["source_chunk_id"] for fact in snapshot_facts
    }
    assert {fact.evidence for fact in bundle.canon_snapshot.facts} == {
        fact["evidence"] for fact in snapshot_facts
    }
    assert manifest.render_version_ids == [render.id for render in bundle.renders]
    assert all((export_root / relative_path).is_file() for relative_path in manifest.files)
    for image_path in exported_images:
        with Image.open(image_path) as image:
            assert image.format == "PNG"
            assert image.size == (320, 480)


@pytest.mark.asyncio
async def test_export_rejects_missing_renders_and_cross_project_episode(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    fixture = Path("tests/fixtures/glass_orchard.md")
    imported = await api_client.post(
        f"/projects/{project_id}/sources",
        files={"file": (fixture.name, fixture.read_bytes(), "text/markdown")},
    )
    chunks = imported.json()["chunks"]
    await api_client.post(f"/projects/{project_id}/canon/extract", json={})
    adapted = await api_client.post(
        f"/projects/{project_id}/episodes/adapt",
        json={
            "source_chunk_ids": [chunk["id"] for chunk in chunks],
            "number": 1,
            "target_format": "storyboard",
        },
    )
    episode = adapted.json()["result"]["episode"]
    scene = adapted.json()["result"]["scenes"][-1]
    await api_client.post(f"/scenes/{scene['id']}/storyboard")

    missing = await api_client.post(
        f"/projects/{project_id}/export",
        json={"episode_id": episode["id"]},
    )
    other = await api_client.post(
        "/projects",
        json={"name": "Another Story", "target_format": "storyboard"},
    )
    crossed = await api_client.post(
        f"/projects/{other.json()['id']}/export",
        json={"episode_id": episode["id"]},
    )

    assert missing.status_code == 409
    assert "render" in missing.json()["detail"].lower()
    assert crossed.status_code == 404
    jobs = (await api_client.get(f"/projects/{project_id}/jobs")).json()
    assert jobs[-1]["kind"] == "export"
    assert jobs[-1]["status"] == "failed"
