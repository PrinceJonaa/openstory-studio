from pathlib import Path

import httpx
import pytest


@pytest.mark.asyncio
async def test_markdown_upload_persists_chunks_with_global_ordinals(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    fixture = Path("tests/fixtures/glass_orchard.md")

    response = await api_client.post(
        f"/projects/{project_id}/sources",
        files={"file": (fixture.name, fixture.read_bytes(), "text/markdown")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["document"]["filename"] == "glass_orchard.md"
    assert Path(payload["document"]["workspace_path"]).read_bytes() == fixture.read_bytes()
    assert [chunk["ordinal"] for chunk in payload["chunks"]] == [1, 2]
    assert [chunk["heading"] for chunk in payload["chunks"]] == [
        "Chapter 1: The Shard",
        "Chapter 2: The Crossing",
    ]

    listed_sources = await api_client.get(f"/projects/{project_id}/sources")
    listed_chunks = await api_client.get(f"/projects/{project_id}/chunks")
    assert [item["id"] for item in listed_sources.json()] == [payload["document"]["id"]]
    assert listed_chunks.json() == payload["chunks"]


@pytest.mark.asyncio
async def test_second_document_continues_project_ordinals(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    markdown = Path("tests/fixtures/glass_orchard.md")
    plaintext = Path("tests/fixtures/glass_orchard.txt")

    first = await api_client.post(
        f"/projects/{project_id}/sources",
        files={"file": (markdown.name, markdown.read_bytes(), "text/markdown")},
    )
    second = await api_client.post(
        f"/projects/{project_id}/sources",
        files={"file": (plaintext.name, plaintext.read_bytes(), "text/plain")},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert [chunk["ordinal"] for chunk in second.json()["chunks"]] == [3, 4]


@pytest.mark.asyncio
async def test_duplicate_source_hash_is_rejected(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    fixture = Path("tests/fixtures/glass_orchard.md")
    upload = {"file": (fixture.name, fixture.read_bytes(), "text/markdown")}

    first = await api_client.post(f"/projects/{project_id}/sources", files=upload)
    duplicate = await api_client.post(f"/projects/{project_id}/sources", files=upload)

    assert first.status_code == 201
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_unsupported_upload_is_rejected_without_persistence(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])

    response = await api_client.post(
        f"/projects/{project_id}/sources",
        files={"file": ("story.pdf", b"not supported", "application/pdf")},
    )

    assert response.status_code == 400
    assert (await api_client.get(f"/projects/{project_id}/sources")).json() == []
