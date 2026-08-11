from collections.abc import Mapping
from typing import Any

from openstory.domain.adaptation import EpisodeAdaptationResponse
from openstory.domain.canon import CanonExtractionResponse
from openstory.domain.storyboard import StoryboardBuildResponse
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
        if schema is StoryboardBuildResponse:
            return schema.model_validate(self._storyboard_response(user_prompt))
        return schema.model_validate({})

    @staticmethod
    def _canon_response(user_prompt: str) -> dict[str, Any]:
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

    @staticmethod
    def _storyboard_response(user_prompt: str) -> dict[str, Any]:
        if "Scene title: The Crossing" not in user_prompt:
            return _generic_storyboard_response(user_prompt)
        return {
            "panels": [
                {
                    "ordinal": 1,
                    "shot_type": "wide",
                    "framing": "establishing, eye-level",
                    "action": "Lira and Ashen arrive at the North Gate.",
                    "visual_description": (
                        "The ward-bound North Gate towers over a reed-choked causeway as "
                        "Lira and Ashen approach in late-afternoon light."
                    ),
                    "character_refs": ["Lira", "Ashen"],
                    "location_ref": "North Gate",
                    "image_prompt": (
                        "Monochrome production storyboard, wide establishing shot of Lira "
                        "and Ashen at the towering ward-bound North Gate, clear silhouettes."
                    ),
                    "negative_prompt": "photorealistic, illegible composition, text artifacts",
                },
                {
                    "ordinal": 2,
                    "shot_type": "medium",
                    "framing": "waist-up, slight low angle",
                    "action": "Lira raises the wrapped Glass Shard in her palm.",
                    "visual_description": (
                        "Lira steps forward and lifts the palm-sized shard toward the gate's "
                        "glass-etched seals; Ashen watches behind her."
                    ),
                    "character_refs": ["Lira", "Ashen"],
                    "location_ref": "North Gate",
                    "image_prompt": (
                        "Storyboard medium shot, Lira raising a wrapped glass shard toward "
                        "etched gate seals, Ashen behind her, readable gesture."
                    ),
                },
                {
                    "ordinal": 3,
                    "shot_type": "medium close-up",
                    "framing": "guard eyeline, reverse angle",
                    "action": "The lead guard blocks the path and questions Lira.",
                    "visual_description": (
                        "A stern guard fills the foreground while Lira holds her ground "
                        "beyond his shoulder."
                    ),
                    "dialogue": [
                        {
                            "speaker_name": "Lead Guard",
                            "text": "State your purpose.",
                        }
                    ],
                    "character_refs": ["Lira"],
                    "location_ref": "North Gate",
                    "image_prompt": (
                        "Storyboard reverse medium close-up, stern gate guard foreground, "
                        "Lira beyond his shoulder, strong eyeline."
                    ),
                },
                {
                    "ordinal": 4,
                    "shot_type": "extreme close-up",
                    "framing": "insert shot, centered",
                    "action": "Cold blue light pulses from the Glass Shard.",
                    "visual_description": (
                        "The shard rests in Lira's palm as a sharp blue pulse catches every "
                        "etched edge and leaps toward the seals."
                    ),
                    "character_refs": ["Lira"],
                    "location_ref": "North Gate",
                    "image_prompt": (
                        "Storyboard insert, extreme close-up of glass shard in Lira's palm, "
                        "blue pulse tracing etched edges, high contrast."
                    ),
                },
                {
                    "ordinal": 5,
                    "shot_type": "two-shot",
                    "framing": "tight profile two-shot",
                    "action": "Ashen leans toward Lira as the wards begin to react.",
                    "visual_description": (
                        "Lira watches the seals while Ashen turns toward her, tension held "
                        "between their profiles and the growing light."
                    ),
                    "dialogue": [
                        {
                            "speaker_ref": "Ashen",
                            "speaker_name": "Ashen",
                            "text": "The wardens will see this.",
                        }
                    ],
                    "character_refs": ["Lira", "Ashen"],
                    "location_ref": "North Gate",
                    "image_prompt": (
                        "Storyboard tight profile two-shot of Lira and Ashen beside glowing "
                        "gate seals, controlled tension, clean staging."
                    ),
                },
                {
                    "ordinal": 6,
                    "shot_type": "wide",
                    "framing": "symmetrical reveal",
                    "action": "The North Gate opens and reveals the passage beyond.",
                    "visual_description": (
                        "The seals flare, the massive gate parts, and Lira and Ashen become "
                        "small silhouettes before the newly opened path."
                    ),
                    "character_refs": ["Lira", "Ashen"],
                    "location_ref": "North Gate",
                    "image_prompt": (
                        "Monochrome storyboard wide reveal, North Gate opening symmetrically, "
                        "Lira and Ashen silhouetted before the passage, luminous seals."
                    ),
                },
            ]
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


def _generic_storyboard_response(user_prompt: str) -> dict[str, Any]:
    summary = "The scene unfolds in six clear visual beats."
    marker = "Scene summary: "
    if marker in user_prompt:
        summary = user_prompt.split(marker, maxsplit=1)[1].splitlines()[0].strip() or summary
    shot_types = ["wide", "medium", "close-up", "insert", "two-shot", "wide"]
    return {
        "panels": [
            {
                "ordinal": index,
                "shot_type": shot_type,
                "framing": "clear production framing",
                "action": f"Visual beat {index} advances the scene.",
                "visual_description": summary,
                "character_refs": [],
                "image_prompt": f"Production storyboard panel {index}: {summary}",
            }
            for index, shot_type in enumerate(shot_types, start=1)
        ]
    }
