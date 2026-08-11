import pytest
from openstory.domain.canon import CanonFact, ExtractedFact
from openstory.domain.ids import new_id
from pydantic import ValidationError


def test_canon_fact_requires_source_chunk() -> None:
    with pytest.raises(ValidationError):
        CanonFact(
            id=new_id(),
            project_id="project",
            subject_entity_id="lira",
            predicate="carries",
            value="glass shard",
            source_chunk_id="",
            evidence="Lira carries the shard.",
            confidence=0.9,
        )


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_canon_fact_confidence_is_bounded(confidence: float) -> None:
    with pytest.raises(ValidationError):
        CanonFact(
            id=new_id(),
            project_id="project",
            subject_entity_id="lira",
            predicate="carries",
            value="glass shard",
            source_chunk_id="chunk",
            evidence="Lira carries the shard.",
            confidence=confidence,
        )


def test_canon_fact_requires_object_or_value() -> None:
    with pytest.raises(ValidationError):
        CanonFact(
            id=new_id(),
            project_id="project",
            subject_entity_id="lira",
            predicate="carries",
            source_chunk_id="chunk",
            evidence="Lira carries the shard.",
            confidence=0.9,
        )


def test_extracted_fact_requires_object_reference_or_value() -> None:
    with pytest.raises(ValidationError):
        ExtractedFact(
            subject_ref="lira",
            predicate="carries",
            evidence="Lira carries the shard.",
            confidence=0.9,
        )


def test_canon_fact_rejects_whitespace_only_evidence() -> None:
    with pytest.raises(ValidationError):
        CanonFact(
            id=new_id(),
            project_id="project",
            subject_entity_id="lira",
            predicate="carries",
            value="glass shard",
            source_chunk_id="chunk",
            evidence="   ",
            confidence=0.9,
        )
