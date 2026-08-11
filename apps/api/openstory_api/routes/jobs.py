from fastapi import APIRouter, HTTPException, status
from openstory.domain.jobs import Job

from openstory_api.dependencies import RepositoryDependency

router = APIRouter(tags=["jobs"])


@router.get("/projects/{project_id}/jobs", response_model=list[Job])
def list_jobs(
    project_id: str,
    repository: RepositoryDependency,
) -> list[Job]:
    if repository.get_project(project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return repository.list_jobs(project_id)


@router.get("/jobs/{job_id}", response_model=Job)
def get_job(
    job_id: str,
    repository: RepositoryDependency,
) -> Job:
    job = repository.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job
