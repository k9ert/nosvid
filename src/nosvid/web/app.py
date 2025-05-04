"""
Web application for nosvid
"""

import logging
import os

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..api.app import app as api_app
from ..services.scheduler_service import SchedulerService

# Set up logging
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="NosVid Web",
    version="1.0.0",
    docs_url=None,  # Disable default /docs endpoint
    redoc_url=None,  # Disable default /redoc endpoint
)

# Mount API
app.mount("/api", api_app)

# Set up templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Store whether cronjobs are enabled
cronjobs_enabled = False


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
    return templates.TemplateResponse(
        "status.html", {"request": request, "cronjobs_enabled": cronjobs_enabled}
    )


@app.get("/swagger", include_in_schema=False)
async def swagger_ui_html():
    """
    Serve Swagger UI for API documentation
    """
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="NosVid API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


def run(port=8000, with_cronjobs=False):
    """
    Run the web application

    Args:
        port: Port to run the server on
        with_cronjobs: Whether to enable scheduled jobs (cronjobs)
    """
    # Update the global cronjobs_enabled variable
    global cronjobs_enabled
    cronjobs_enabled = with_cronjobs

    if with_cronjobs:
        # Initialize and start the scheduler service
        scheduler = SchedulerService()
        logger.info("Initializing scheduler service")

        # Log all scheduled jobs
        jobs = scheduler.get_all_jobs()
        if jobs:
            logger.info(f"Scheduled jobs: {len(jobs)}")
            for job in jobs:
                next_run = job.get("next_run", "Not scheduled")
                logger.info(
                    f"  - {job['id']}: {job['description']} (Next run: {next_run})"
                )
        else:
            logger.info("No scheduled jobs configured")
    else:
        logger.info("Scheduled jobs (cronjobs) are disabled")

    # Start the web server
    import uvicorn

    logger.info(f"Starting web server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
