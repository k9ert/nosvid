"""
Status API endpoints
"""

from fastapi import APIRouter, Depends
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
