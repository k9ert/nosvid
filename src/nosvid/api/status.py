"""
Status API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from ..services.scheduler_service import SchedulerService

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
def enable_job(job_id: str, scheduler: SchedulerService = Depends(get_scheduler_service)):
    """
    Enable a job
    """
    success = scheduler.enable_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to enable job {job_id}")
    return {"message": f"Job {job_id} enabled successfully"}

@router.post("/jobs/{job_id}/disable")
def disable_job(job_id: str, scheduler: SchedulerService = Depends(get_scheduler_service)):
    """
    Disable a job
    """
    success = scheduler.disable_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to disable job {job_id}")
    return {"message": f"Job {job_id} disabled successfully"}
