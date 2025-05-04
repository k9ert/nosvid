"""
Cron job API endpoints
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..services.scheduler_service import SchedulerService

# Create router
router = APIRouter()


# Models
class CronJobBase(BaseModel):
    """Base model for cron jobs"""

    command: str
    args: List[str] = []
    schedule: str
    enabled: bool = True
    description: str = ""


class CronJobCreate(CronJobBase):
    """Model for creating a cron job"""

    id: str


class CronJobUpdate(BaseModel):
    """Model for updating a cron job"""

    command: Optional[str] = None
    args: Optional[List[str]] = None
    schedule: Optional[str] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None


class CronJobResponse(CronJobBase):
    """Response model for a cron job"""

    id: str
    next_run: Optional[str] = None


# Dependency
def get_scheduler_service():
    """Get the scheduler service"""
    return SchedulerService()


# Routes
@router.get("/jobs", response_model=List[CronJobResponse])
def list_jobs(scheduler: SchedulerService = Depends(get_scheduler_service)):
    """
    List all cron jobs
    """
    return scheduler.get_all_jobs()


@router.get("/jobs/{job_id}", response_model=CronJobResponse)
def get_job(job_id: str, scheduler: SchedulerService = Depends(get_scheduler_service)):
    """
    Get a cron job by ID
    """
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.post("/jobs", response_model=CronJobResponse)
def create_job(
    job: CronJobCreate, scheduler: SchedulerService = Depends(get_scheduler_service)
):
    """
    Create a new cron job
    """
    success = scheduler.add_job(
        job_id=job.id,
        command=job.command,
        args=job.args,
        cron_expression=job.schedule,
        enabled=job.enabled,
        description=job.description,
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to create job")

    return scheduler.get_job(job.id)


@router.put("/jobs/{job_id}", response_model=CronJobResponse)
def update_job(
    job_id: str,
    job: CronJobUpdate,
    scheduler: SchedulerService = Depends(get_scheduler_service),
):
    """
    Update a cron job
    """
    if not scheduler.get_job(job_id):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    success = scheduler.update_job(
        job_id=job_id,
        command=job.command,
        args=job.args,
        cron_expression=job.schedule,
        enabled=job.enabled,
        description=job.description,
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to update job")

    return scheduler.get_job(job_id)


@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: str, scheduler: SchedulerService = Depends(get_scheduler_service)
):
    """
    Delete a cron job
    """
    if not scheduler.get_job(job_id):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    success = scheduler.remove_job(job_id)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete job")

    return {"message": f"Job {job_id} deleted successfully"}
