from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from pydantic import BaseModel


async def import_glass_orchard(
    api_client: httpx.AsyncClient,
    project_id: str,
) -> dict[str, Any]:
    fixture = Path("tests/fixtures/glass_orchard.md")
    response = await api_client.post(
        f"/projects/{project_id}/sources",
        files={"file": (fixture.name, fixture.read_bytes(), "text/markdown")},
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_source_to_canon_vertical_slice_preserves_provenance(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    imported = await import_glass_orchard(api_client, project_id)
    chapter_one = imported["chunks"][0]

    extracted = await api_client.post(f"/projects/{project_id}/canon/extract", json={})

    assert extracted.status_code == 200
    payload = extracted.json()
    assert payload["job"]["status"] == "succeeded"
    assert payload["job"]["progress_current"] == 2
    assert payload["job"]["progress_total"] == 2

    entities_response = await api_client.get(f"/projects/{project_id}/entities")
    facts_response = await api_client.get(f"/projects/{project_id}/facts")
    assert entities_response.status_code == 200
    assert facts_response.status_code == 200
    entities = entities_response.json()
    facts = facts_response.json()

    by_name = {entity["canonical_name"]: entity for entity in entities}
    assert by_name["Lira"]["kind"] == "character"
    assert by_name["North Gate"]["kind"] == "location"
    assert by_name["Glass Shard"]["kind"] == "object"

    ownership = next(fact for fact in facts if fact["predicate"] == "belongs_to")
    assert ownership["subject_entity_id"] == by_name["Glass Shard"]["id"]
    assert ownership["object_entity_id"] == by_name["Lira"]["id"]
    assert ownership["source_chunk_id"] == chapter_one["id"]
    assert ownership["evidence"] in chapter_one["text"]
    assert ownership["confidence"] == pytest.approx(0.96)

    jobs = await api_client.get(f"/projects/{project_id}/jobs")
    fetched_job = await api_client.get(f"/jobs/{payload['job']['id']}")
    assert [job["id"] for job in jobs.json()] == [payload["job"]["id"]]
    assert fetched_job.json() == payload["job"]


@pytest.mark.asyncio
async def test_canon_extraction_can_be_limited_to_selected_chunks(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
) -> None:
    project_id = str(api_project["id"])
    imported = await import_glass_orchard(api_client, project_id)
    chapter_one_id = imported["chunks"][0]["id"]

    response = await api_client.post(
        f"/projects/{project_id}/canon/extract",
        json={"chunk_ids": [chapter_one_id]},
    )

    assert response.status_code == 200
    assert response.json()["job"]["progress_total"] == 1
    entities = (await api_client.get(f"/projects/{project_id}/entities")).json()
    assert "North Gate" not in {entity["canonical_name"] for entity in entities}


class FabricatedEvidenceProvider:
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
        temperature: float = 0.2,
    ) -> BaseModel:
        del system_prompt, user_prompt, temperature
        return schema.model_validate(
            {
                "entities": [
                    {
                        "ref": "lira",
                        "kind": "character",
                        "canonical_name": "Lira",
                    }
                ],
                "facts": [
                    {
                        "subject_ref": "lira",
                        "predicate": "owns",
                        "value": "a crown",
                        "evidence": "Lira owned the moon crown.",
                        "confidence": 0.99,
                    }
                ],
                "unresolved_references": [],
            }
        )


@pytest.mark.asyncio
async def test_extraction_rejects_fabricated_evidence_and_records_failed_job(
    api_client: httpx.AsyncClient,
    api_project: dict[str, object],
    api_app: FastAPI,
) -> None:
    project_id = str(api_project["id"])
    await import_glass_orchard(api_client, project_id)
    api_app.state.text_provider = FabricatedEvidenceProvider()

    response = await api_client.post(f"/projects/{project_id}/canon/extract", json={})

    assert response.status_code == 422
    assert "does not occur in source chunk" in response.json()["detail"]
    assert (await api_client.get(f"/projects/{project_id}/entities")).json() == []
    assert (await api_client.get(f"/projects/{project_id}/facts")).json() == []
    jobs = (await api_client.get(f"/projects/{project_id}/jobs")).json()
    assert len(jobs) == 1
    assert jobs[0]["status"] == "failed"
    assert "does not occur in source chunk" in jobs[0]["error"]
