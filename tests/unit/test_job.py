from datetime import UTC, datetime

import pytest
from pydantic import ValidationError


def test_new_job_defaults_to_queued_with_zero_progress() -> None:
    from openstory.domain.jobs import Job, JobKind, JobStatus

    timestamp = datetime(2026, 8, 10, tzinfo=UTC)
    job = Job(
        id="job-1",
        project_id="project-1",
        kind=JobKind.CANON_EXTRACT,
        created_at=timestamp,
        updated_at=timestamp,
    )

    assert job.status is JobStatus.QUEUED
    assert job.progress_current == 0
    assert job.progress_total is None
    assert job.error is None


def test_job_progress_cannot_exceed_total() -> None:
    from openstory.domain.jobs import Job, JobKind

    timestamp = datetime(2026, 8, 10, tzinfo=UTC)
    with pytest.raises(ValidationError):
        Job(
            id="job-1",
            project_id="project-1",
            kind=JobKind.IMAGE_RENDER,
            progress_current=2,
            progress_total=1,
            created_at=timestamp,
            updated_at=timestamp,
        )

