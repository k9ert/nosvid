"""
Web application for nosvid
"""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..api.app import app as api_app
from ..services.scheduler_service import SchedulerService

# Set up logging
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(title="NosVid Web", version="1.0.0")

# Mount API
app.mount("/api", api_app)

# Set up templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Render the index page
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/status", response_class=HTMLResponse)
async def status(request: Request):
    """
    Render the status page
    """
    return templates.TemplateResponse("status.html", {"request": request})

def run(port=8000):
    """
    Run the web application

    Args:
        port: Port to run the server on
    """
    # Initialize and start the scheduler service
    scheduler = SchedulerService()
    logger.info("Initializing scheduler service")

    # Log all scheduled jobs
    jobs = scheduler.get_all_jobs()
    if jobs:
        logger.info(f"Scheduled jobs: {len(jobs)}")
        for job in jobs:
            next_run = job.get('next_run', 'Not scheduled')
            logger.info(f"  - {job['id']}: {job['description']} (Next run: {next_run})")
    else:
        logger.info("No scheduled jobs configured")

    # Start the web server
    import uvicorn
    logger.info(f"Starting web server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
