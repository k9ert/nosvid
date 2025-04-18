"""
Web application for nosvid
"""

import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..api.app import app as api_app

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

def run(port=8000):
    """
    Run the web application

    Args:
        port: Port to run the server on
    """
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
