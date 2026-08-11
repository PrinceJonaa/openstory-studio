from collections.abc import Awaitable, Callable
from typing import TypeVar

from openstory.domain.ids import new_id
from openstory.domain.jobs import Job, JobKind, JobRunResult, JobStatus
from openstory.domain.project import utc_now
from openstory.persistence.repositories import OpenStoryRepository

T = TypeVar("T")


class RunJobService:
    def __init__(self, repository: OpenStoryRepository) -> None:
        self.repository = repository

    async def run(
        self,
        project_id: str,
        kind: JobKind,
        operation: Callable[[], Awaitable[T]],
        progress_total: int | None = None,
    ) -> JobRunResult[T]:
        queued = Job(
            id=new_id(),
            project_id=project_id,
            kind=kind,
            progress_total=progress_total,
        )
        self.repository.add_job(queued)
        running = queued.model_copy(
            update={"status": JobStatus.RUNNING, "updated_at": utc_now()}
        )
        self.repository.update_job(running)

        try:
            result = await operation()
        except Exception as error:
            self.repository.rollback()
            concise_error = (str(error).strip() or type(error).__name__)[:4_000]
            failed = running.model_copy(
                update={
                    "status": JobStatus.FAILED,
                    "error": concise_error,
                    "updated_at": utc_now(),
                }
            )
            self.repository.update_job(failed)
            raise

        succeeded = running.model_copy(
            update={
                "status": JobStatus.SUCCEEDED,
                "progress_current": progress_total or 0,
                "updated_at": utc_now(),
            }
        )
        self.repository.update_job(succeeded)
        return JobRunResult(job=succeeded, result=result)
