from pathlib import Path

import pytest
from openstory.domain.canon import CanonExtractionResponse
from openstory.providers.text.mock import MockTextProvider
from pydantic import ValidationError


@pytest.mark.asyncio
async def test_mock_provider_is_deterministic() -> None:
    source = Path("tests/fixtures/glass_orchard.md").read_text()
    prompt = f"Project: The Glass Orchard\n\n{source}"
    provider = MockTextProvider()

    first = await provider.generate_structured(
        system_prompt="archivist",
        user_prompt=prompt,
        schema=CanonExtractionResponse,
    )
    second = await provider.generate_structured(
        system_prompt="archivist",
        user_prompt=prompt,
        schema=CanonExtractionResponse,
    )

    assert first == second
    assert {entity.canonical_name for entity in first.entities} >= {
        "Lira",
        "North Gate",
        "Glass Shard",
    }
    assert all(fact.evidence in source for fact in first.facts)


@pytest.mark.asyncio
async def test_mock_provider_returns_an_unresolved_reference_for_unknown_text() -> None:
    response = await MockTextProvider().generate_structured(
        system_prompt="archivist",
        user_prompt="Project: Unknown\n\nNothing from the fixture.",
        schema=CanonExtractionResponse,
    )

    assert response.entities == []
    assert response.facts == []
    assert response.unresolved_references == [
        "Mock mode has no fixture extraction for this source chunk."
    ]


@pytest.mark.asyncio
async def test_mock_provider_validates_response_overrides() -> None:
    provider = MockTextProvider(
        {
            "CanonExtractionResponse": {
                "entities": [],
                "facts": [
                    {
                        "subject_ref": "lira",
                        "predicate": "exists",
                        "value": True,
                        "evidence": "Lira exists.",
                        "confidence": 2,
                    }
                ],
                "unresolved_references": [],
            }
        }
    )

    with pytest.raises(ValidationError):
        await provider.generate_structured(
            system_prompt="archivist",
            user_prompt="Lira exists.",
            schema=CanonExtractionResponse,
        )
