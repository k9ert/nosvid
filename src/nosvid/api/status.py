"""
Status API endpoints
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from ..services.scheduler_service import SchedulerService
from ..services.video_service import download_status
from .models import DownloadStatusResponse

# Create router
router = APIRouter()


# Dependency
def get_scheduler_service():
    """Get the scheduler service"""
    return SchedulerService()


@router.get("/jobs", response_model=List[Dict[str, Any]])
def get_jobs(scheduler: SchedulerService = Depends(get_scheduler_service)):
    """
    Get all scheduled jobs
    """
    return scheduler.get_all_jobs()


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
def get_job(job_id: str, scheduler: SchedulerService = Depends(get_scheduler_service)):
    """
    Get a job by ID
    """
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.post("/jobs/{job_id}/enable")
def enable_job(
    job_id: str, scheduler: SchedulerService = Depends(get_scheduler_service)
):
    """
    Enable a job
    """
    success = scheduler.enable_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to enable job {job_id}")
    return {"message": f"Job {job_id} enabled successfully"}


@router.post("/jobs/{job_id}/disable")
def disable_job(
    job_id: str, scheduler: SchedulerService = Depends(get_scheduler_service)
):
    """
    Disable a job
    """
    success = scheduler.disable_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to disable job {job_id}")
    return {"message": f"Job {job_id} disabled successfully"}


@router.get("/download", response_model=DownloadStatusResponse, tags=["status"])
def get_download_status():
    """
    Get the current download status

    This endpoint returns information about any ongoing download operations.

    The response includes:
    - **in_progress**: Whether a download is currently in progress
    - **video_id**: The ID of the video being downloaded (if any)
    - **started_at**: When the download started (ISO format)
    - **user**: Identifier for the user who initiated the download

    This endpoint is useful for monitoring download progress and preventing
    concurrent downloads that could cause conflicts.
    """
    return download_status
