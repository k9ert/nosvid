"""
FastAPI application for nosvid
"""

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import routers
from .routers import platforms, statistics, videos
from .status import router as status_router

# Set up logging
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="NosVid API",
    version="1.0.0",
    description="API for managing YouTube videos with NosVid",
    openapi_tags=[
        {"name": "videos", "description": "Operations with videos"},
        {"name": "platforms", "description": "Platform-specific operations"},
        {"name": "status", "description": "Status and scheduled jobs"},
        {"name": "statistics", "description": "Repository statistics"},
    ],
)


# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle all unhandled exceptions and log them with stacktraces
    """
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(f"Stack trace: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    Handle ValueError exceptions (including platform activation errors)
    """
    logger.error(f"ValueError: {str(exc)}")
    logger.error(f"Stack trace: {traceback.format_exc()}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions
    """
    logger.error(f"HTTP exception: {str(exc.detail)}")
    logger.error(f"Stack trace: {traceback.format_exc()}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors
    """
    logger.error(f"Validation error: {str(exc)}")
    logger.error(f"Stack trace: {traceback.format_exc()}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


# Include routers
app.include_router(videos.router, prefix="/videos", tags=["videos"])
app.include_router(platforms.router, prefix="/videos", tags=["platforms"])
app.include_router(status_router, prefix="/status", tags=["status"])
app.include_router(statistics.router, prefix="/statistics", tags=["statistics"])
