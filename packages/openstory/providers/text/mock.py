from collections.abc import Mapping
from typing import Any

from openstory.domain.adaptation import EpisodeAdaptationResponse
from openstory.domain.canon import CanonExtractionResponse
from openstory.providers.text.base import T

CHAPTER_ONE_CARRY_EVIDENCE = (
    "Lira Vale carried a palm-sized Glass Shard wrapped in blue cloth."
)
CHAPTER_ONE_OWNERSHIP_EVIDENCE = (
    "The Glass Shard\nbelonged to Lira, a keepsake left by her mother."
)
CHAPTER_TWO_ARRIVAL_EVIDENCE = (
    "At late afternoon, Lira and Ashen reached the North Gate."
)
CHAPTER_TWO_OPENING_EVIDENCE = (
    "Its cold blue pulse crossed the glass-etched seals, and the North Gate opened."
)


class MockTextProvider:
    def __init__(
        self,
        response_overrides: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> None:
        self.response_overrides = dict(response_overrides or {})

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
        temperature: float = 0.2,
    ) -> T:
        del system_prompt, temperature
        override = self.response_overrides.get(schema.__name__)
        if override is not None:
            return schema.model_validate(override)
        if schema is CanonExtractionResponse:
            return schema.model_validate(self._canon_response(user_prompt))
        if schema is EpisodeAdaptationResponse:
            return schema.model_validate(self._episode_response(user_prompt))
        return schema.model_validate({})

    @staticmethod
    def _canon_response(user_prompt: str) -> dict[str, Any]:
        if "The Glass Orchard" not in user_prompt:
            return _unknown_response()

        entities: list[dict[str, Any]] = []
        facts: list[dict[str, Any]] = []
        if CHAPTER_ONE_CARRY_EVIDENCE in user_prompt:
            entities.extend(
                [
                    {
                        "ref": "lira",
                        "kind": "character",
                        "canonical_name": "Lira",
                        "aliases": ["Lira Vale"],
                        "summary": "Bearer of the Glass Shard.",
                    },
                    {
                        "ref": "glass_shard",
                        "kind": "object",
                        "canonical_name": "Glass Shard",
                        "summary": "A palm-sized keepsake wrapped in blue cloth.",
                    },
                    {
                        "ref": "ashen",
                        "kind": "character",
                        "canonical_name": "Ashen",
                    },
                ]
            )
            facts.extend(
                [
                    {
                        "subject_ref": "lira",
                        "predicate": "carries",
                        "object_ref": "glass_shard",
                        "evidence": CHAPTER_ONE_CARRY_EVIDENCE,
                        "confidence": 0.98,
                    },
                    {
                        "subject_ref": "glass_shard",
                        "predicate": "belongs_to",
                        "object_ref": "lira",
                        "evidence": CHAPTER_ONE_OWNERSHIP_EVIDENCE,
                        "confidence": 0.96,
                    },
                ]
            )

        if CHAPTER_TWO_ARRIVAL_EVIDENCE in user_prompt:
            entities.extend(
                [
                    {
                        "ref": "lira",
                        "kind": "character",
                        "canonical_name": "Lira",
                        "aliases": ["Lira Vale"],
                    },
                    {
                        "ref": "ashen",
                        "kind": "character",
                        "canonical_name": "Ashen",
                    },
                    {
                        "ref": "north_gate",
                        "kind": "location",
                        "canonical_name": "North Gate",
                        "summary": "A ward-bound city gate above a reed-choked causeway.",
                    },
                    {
                        "ref": "glass_shard",
                        "kind": "object",
                        "canonical_name": "Glass Shard",
                    },
                ]
            )
            facts.extend(
                [
                    {
                        "subject_ref": "lira",
                        "predicate": "reached",
                        "object_ref": "north_gate",
                        "evidence": CHAPTER_TWO_ARRIVAL_EVIDENCE,
                        "confidence": 0.98,
                    },
                    {
                        "subject_ref": "ashen",
                        "predicate": "reached",
                        "object_ref": "north_gate",
                        "evidence": CHAPTER_TWO_ARRIVAL_EVIDENCE,
                        "confidence": 0.98,
                    },
                    {
                        "subject_ref": "north_gate",
                        "predicate": "opened_in_response_to",
                        "value": "Glass Shard cold blue pulse",
                        "evidence": CHAPTER_TWO_OPENING_EVIDENCE,
                        "confidence": 0.97,
                    },
                ]
            )

        if not entities:
            return _unknown_response()
        return {
            "entities": entities,
            "facts": facts,
            "unresolved_references": [],
        }

    @staticmethod
    def _episode_response(user_prompt: str) -> dict[str, Any]:
        has_shard = CHAPTER_ONE_CARRY_EVIDENCE in user_prompt
        has_crossing = CHAPTER_TWO_ARRIVAL_EVIDENCE in user_prompt
        scenes: list[dict[str, Any]] = []
        if has_shard:
            scenes.append(
                {
                    "ordinal": len(scenes) + 1,
                    "title": "The Shard Awakens",
                    "purpose": "Introduce Lira, Ashen, and the shard's dangerous response.",
                    "character_refs": ["Lira", "Ashen"],
                    "summary": (
                        "Lira reveals the Glass Shard and wakes its cold blue light; "
                        "Ashen warns that the wardens may notice."
                    ),
                }
            )
        if has_crossing:
            scenes.append(
                {
                    "ordinal": len(scenes) + 1,
                    "title": "The Crossing",
                    "purpose": "Turn the shard's power into a visible crossing of the city wards.",
                    "location_ref": "North Gate",
                    "character_refs": ["Lira", "Ashen"],
                    "summary": (
                        "At the North Gate, Lira raises the Glass Shard; its pulse crosses "
                        "the seals and opens the way."
                    ),
                }
            )
        if scenes:
            title = "The Crossing" if has_crossing else "The Shard"
            return {
                "episode": {
                    "title": title,
                    "logline": (
                        "Lira risks exposing a mysterious heirloom to pass a ward-bound gate."
                    ),
                    "adaptation_notes": (
                        "Omissions: incidental guard dialogue is compressed. "
                        "Reordering: none; causal order is preserved."
                    ),
                },
                "scenes": scenes,
            }

        first_sentence = _first_source_sentence(user_prompt)
        return {
            "episode": {
                "title": "Adapted Episode",
                "logline": first_sentence,
                "adaptation_notes": "Omissions: none. Reordering: none.",
            },
            "scenes": [
                {
                    "ordinal": 1,
                    "title": "Opening Beat",
                    "purpose": "Visualize the first explicit source beat.",
                    "summary": first_sentence,
                    "character_refs": [],
                }
            ],
        }


def _unknown_response() -> dict[str, Any]:
    return {
        "entities": [],
        "facts": [],
        "unresolved_references": [
            "Mock mode has no fixture extraction for this source chunk."
        ],
    }


def _first_source_sentence(user_prompt: str) -> str:
    source = user_prompt.split("SOURCE CHUNKS:\n", maxsplit=1)[-1]
    for line in source.splitlines():
        candidate = line.strip()
        if not candidate or candidate.startswith(("---", "#", "_")):
            continue
        return candidate[:2_000]
    return "The selected source begins with a quiet visual beat."
