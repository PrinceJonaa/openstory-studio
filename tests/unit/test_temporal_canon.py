from collections.abc import Iterator
from pathlib import Path

import pytest
from openstory.application.create_project import CreateProjectService
from openstory.application.ingest_source import IngestSourceService
from openstory.domain.canon import CanonFact, ExtractedEntity
from openstory.domain.ids import new_id
from openstory.domain.project import ProjectCreate
from openstory.persistence.db import create_db_engine, init_db, make_session_factory
from openstory.persistence.models import CanonFactRecord
from openstory.persistence.repositories import OpenStoryRepository
from openstory.services.workspace import WorkspaceManager
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def repository_with_temporal_fact(
    tmp_path: Path,
) -> Iterator[tuple[OpenStoryRepository, str, str, str, str]]:
    engine = create_db_engine(f"sqlite+pysqlite:///{tmp_path / 'openstory.db'}")
    init_db(engine)
    session_factory = make_session_factory(engine)
    workspace = WorkspaceManager(tmp_path / "workspaces")

    with session_factory() as session:
        repository = OpenStoryRepository(session)
        project = CreateProjectService(repository, workspace).execute(
            ProjectCreate(name="Temporal Story", target_format="storyboard")
        )
        ingestion = IngestSourceService(repository, workspace).execute(
            project.id,
            "story.txt",
            b"Chapter 1\nWeed owns Sword A.",
        )
        weed = repository.resolve_entity(
            project.id,
            ExtractedEntity(
                ref="weed",
                kind="character",
                canonical_name="Weed",
            ),
        )
        sword = repository.resolve_entity(
            project.id,
            ExtractedEntity(
                ref="sword",
                kind="object",
                canonical_name="Sword A",
            ),
        )
        fact = CanonFact(
            id=new_id(),
            project_id=project.id,
            subject_entity_id=weed.id,
            predicate="owns",
            object_entity_id=sword.id,
            valid_from_ordinal=3,
            valid_to_ordinal=17,
            source_chunk_id=ingestion.chunks[0].id,
            evidence="Weed owns Sword A.",
            confidence=1,
        )
        repository.add_canon_fact(fact)
        repository.commit()
        yield repository, project.id, weed.id, sword.id, ingestion.chunks[0].id

    engine.dispose()


@pytest.mark.parametrize(
    ("ordinal", "expected_predicates"),
    [
        (2, []),
        (3, ["owns"]),
        (10, ["owns"]),
        (17, ["owns"]),
        (18, []),
    ],
)
def test_temporal_fact_uses_inclusive_range(
    repository_with_temporal_fact: tuple[OpenStoryRepository, str, str, str, str],
    ordinal: int,
    expected_predicates: list[str],
) -> None:
    repository, project_id, weed_id, sword_id, _chunk_id = repository_with_temporal_fact

    snapshot = repository.get_canon_snapshot(project_id, ordinal)

    assert [fact.predicate for fact in snapshot.facts] == expected_predicates
    expected_entity_ids = {weed_id, sword_id} if expected_predicates else set()
    assert {entity.id for entity in snapshot.entities} == expected_entity_ids


def test_unbounded_fact_is_active_at_every_nonnegative_ordinal(
    repository_with_temporal_fact: tuple[OpenStoryRepository, str, str, str, str],
) -> None:
    repository, project_id, weed_id, _sword_id, chunk_id = repository_with_temporal_fact
    repository.add_canon_fact(
        CanonFact(
            id=new_id(),
            project_id=project_id,
            subject_entity_id=weed_id,
            predicate="exists",
            value=True,
            source_chunk_id=chunk_id,
            evidence="Weed owns Sword A.",
            confidence=0.8,
        )
    )
    repository.commit()

    assert [fact.predicate for fact in repository.get_canon_snapshot(project_id, 0).facts] == [
        "exists"
    ]
    assert [fact.predicate for fact in repository.get_canon_snapshot(project_id, 999).facts] == [
        "exists"
    ]


@pytest.mark.parametrize(
    ("valid_from", "valid_to"),
    [(-1, None), (None, -1), (18, 17)],
)
def test_canon_fact_rejects_invalid_temporal_ranges(
    valid_from: int | None,
    valid_to: int | None,
) -> None:
    with pytest.raises(ValidationError):
        CanonFact(
            id=new_id(),
            project_id="project",
            subject_entity_id="weed",
            predicate="owns",
            value="Sword A",
            valid_from_ordinal=valid_from,
            valid_to_ordinal=valid_to,
            source_chunk_id="chunk",
            evidence="Weed owns Sword A.",
            confidence=1,
        )


def test_database_rejects_reversed_temporal_range(
    repository_with_temporal_fact: tuple[OpenStoryRepository, str, str, str, str],
) -> None:
    repository, project_id, weed_id, sword_id, chunk_id = repository_with_temporal_fact
    repository.session.add(
        CanonFactRecord(
            id=new_id(),
            project_id=project_id,
            subject_entity_id=weed_id,
            predicate="owns",
            object_entity_id=sword_id,
            value=None,
            valid_from_ordinal=18,
            valid_to_ordinal=17,
            source_chunk_id=chunk_id,
            evidence="Weed owns Sword A.",
            confidence=1,
        )
    )

    with pytest.raises(IntegrityError):
        repository.commit()
    repository.rollback()
