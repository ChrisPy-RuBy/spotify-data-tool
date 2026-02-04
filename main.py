"""Spotify Data Tool - FastAPI Web Application.

A web application for visualizing and exploring Spotify data with interactive
charts and dashboards.
"""

import atexit
import shutil
import tempfile
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api import analytics, playlists, tracks
from src.loaders import DataLoader

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB


class AppState:
    """Mutable container for the currently loaded dataset."""

    def __init__(self):
        self.loader: DataLoader | None = None
        self._temp_dir: Path | None = None

    def load_from_directory(self, data_dir: Path):
        """Create a new DataLoader from an extracted data directory."""
        self._cleanup_temp()
        self._temp_dir = data_dir
        self.loader = DataLoader(data_dir)

    def reset(self):
        """Clear the current dataset."""
        self._cleanup_temp()
        self.loader = None

    @property
    def is_loaded(self) -> bool:
        return self.loader is not None

    def _cleanup_temp(self):
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
            self._temp_dir = None


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    app_state.reset()


# Initialize FastAPI app
app = FastAPI(
    title="Spotify Data Tool",
    description="Visualize and explore your Spotify data",
    version="0.1.0",
    lifespan=lifespan,
)

# Also register atexit for non-graceful shutdowns
atexit.register(app_state.reset)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory="src/templates")


# Dependency to get data loader
def get_data_loader() -> DataLoader:
    """Get the data loader from app state, or raise if no data loaded."""
    if not app_state.is_loaded:
        raise HTTPException(status_code=403, detail="No data loaded")
    return app_state.loader


# Middleware to gate all routes behind data availability
ALLOWED_PATHS = ("/upload", "/static", "/api/upload", "/api/reset", "/health")


@app.middleware("http")
async def require_data(request: Request, call_next):
    """Redirect to upload page if no data is loaded."""
    if not app_state.is_loaded and not any(
        request.url.path.startswith(p) for p in ALLOWED_PATHS
    ):
        return RedirectResponse(url="/upload")
    return await call_next(request)


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


# Upload endpoint
@app.post("/api/upload")
async def upload_data(file: UploadFile):
    """Accept a Spotify data export zip file, validate, extract, and load it."""
    # Read the file content
    content = await file.read()

    # Check file size
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413, detail="File too large. Maximum size is 50MB."
        )

    # Write to a temporary file to validate as zip
    tmp_zip = Path(tempfile.mktemp(suffix=".zip"))
    try:
        tmp_zip.write_bytes(content)

        if not zipfile.is_zipfile(tmp_zip):
            raise HTTPException(
                status_code=400, detail="Uploaded file is not a valid zip archive."
            )

        with zipfile.ZipFile(tmp_zip, "r") as zf:
            # Check for path traversal
            for name in zf.namelist():
                if ".." in name or name.startswith("/"):
                    raise HTTPException(
                        status_code=400,
                        detail="Zip file contains unsafe path entries.",
                    )

            # Validate that it contains at least Playlist1.json.json
            names = zf.namelist()
            if "Playlist1.json.json" not in names:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid Spotify data export: missing Playlist1.json.json. "
                    "Please upload the zip file from your Spotify data export.",
                )

            # Extract to a temporary directory
            extract_dir = Path(tempfile.mkdtemp(prefix="spotify_data_"))
            zf.extractall(extract_dir)

        # Load the data
        app_state.load_from_directory(extract_dir)

    finally:
        # Clean up the temporary zip file
        if tmp_zip.exists():
            tmp_zip.unlink()

    return RedirectResponse(url="/", status_code=303)


# Reset endpoint
@app.post("/api/reset")
async def reset_data():
    """Clear the current dataset and redirect to upload page."""
    app_state.reset()
    return RedirectResponse(url="/upload", status_code=303)


# Upload page route
@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request, error: str | None = None):
    """Upload page — shown when no data is loaded."""
    return templates.TemplateResponse(
        "upload.html", {"request": request, "error": error}
    )


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
    return {
        "status": "healthy",
        "service": "spotify-data-tool",
        "data_loaded": app_state.is_loaded,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
