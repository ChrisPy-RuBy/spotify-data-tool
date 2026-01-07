"""Spotify Data Tool - FastAPI Web Application.

A web application for visualizing and exploring Spotify data with interactive
charts and dashboards.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api import analytics, playlists, tracks
from src.loaders import DataLoader

# Initialize FastAPI app
app = FastAPI(
    title="Spotify Data Tool",
    description="Visualize and explore your Spotify data",
    version="0.1.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory="src/templates")

# Initialize singleton data loader
data_dir = Path("data")
data_loader = DataLoader(data_dir)


# Dependency to get data loader
def get_data_loader() -> DataLoader:
    """Get the singleton data loader instance."""
    return data_loader


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    """Handle file not found errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Data file not found. Please ensure data files are in the 'data' directory.",
            "detail": str(exc),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred",
            "detail": str(exc),
            "type": type(exc).__name__,
        },
    )


# Include API routers
app.include_router(playlists.router, prefix="/api/playlists", tags=["playlists"])
app.include_router(tracks.router, prefix="/api/tracks", tags=["tracks"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


# Page routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page / dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/playlists", response_class=HTMLResponse)
async def playlists_page(request: Request):
    """Playlists browsing page."""
    return templates.TemplateResponse("playlists.html", {"request": request})


@app.get("/tracks", response_class=HTMLResponse)
async def tracks_page(request: Request):
    """Tracks browsing page."""
    return templates.TemplateResponse("tracks.html", {"request": request})


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Analytics dashboard page."""
    return templates.TemplateResponse("analytics.html", {"request": request})


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "spotify-data-tool"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
