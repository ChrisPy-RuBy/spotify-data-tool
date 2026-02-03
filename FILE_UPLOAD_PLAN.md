# File Upload: Technical Discussion

## Goal

Replace the current static `data/` directory approach with user-driven file upload. The app should be unusable until a Spotify data export (zip file) is uploaded, and it should be possible to reset and upload a new file without restarting the server.

## Current Architecture

- `main.py` creates a singleton `DataLoader(Path("data"))` at startup
- `DataLoader` reads JSON files from the data directory and caches parsed results in memory (`_cache` dict)
- API routes obtain the `DataLoader` via FastAPI dependency injection (`Depends(get_data_loader)`)
- Analytics functions receive raw dicts from the loader
- Templates fetch data from API endpoints using JavaScript

The key coupling point is the singleton `DataLoader` created at module level in `main.py` and imported by route modules.

## Spotify Data Export Format

Spotify provides a zip file containing JSON files at the top level:

- `Playlist1.json.json` — all playlists with track listings
- `StreamingHistory_music_*.json.json` — listening history (one or more files)
- `YourLibrary.json.json` — saved/liked tracks
- Various other files (podcasts, search queries, etc.)

The double `.json.json` extension is how Spotify names these files.

## Proposed Design

### 1. Session-based data storage

Hold the uploaded data in a server-side session object rather than a global singleton. This keeps the architecture simple (single-user tool) while allowing reset without restart.

```python
class AppState:
    """Mutable container for the currently loaded dataset."""

    def __init__(self):
        self.loader: DataLoader | None = None

    def load_from_directory(self, data_dir: Path):
        """Create a new DataLoader from an extracted data directory."""
        self.loader = DataLoader(data_dir)

    def reset(self):
        """Clear the current dataset."""
        self.loader = None

    @property
    def is_loaded(self) -> bool:
        return self.loader is not None
```

`main.py` creates a single `AppState()` instance. The existing `get_data_loader` dependency changes to pull from `app_state.loader` and returns a 403/redirect if no data is loaded.

### 2. Upload and extraction flow

Add a new route that accepts a zip file via multipart form upload (`python-multipart` is already a dependency):

1. Receive the zip file
2. Validate it contains the expected JSON files (at minimum `Playlist1.json.json`)
3. Extract to a temporary directory (use `tempfile.mkdtemp()`)
4. Create a new `DataLoader` pointing at the extracted directory
5. Store it in `AppState`

```
POST /api/upload
Content-Type: multipart/form-data
Body: file=<spotify_export.zip>
```

On success, redirect to the main page. On failure, return to the upload page with an error message.

### 3. Gate all routes behind data availability

Two approaches, in order of preference:

**Option A: FastAPI dependency that raises**

Modify `get_data_loader` to check `app_state.is_loaded`. If not loaded, raise an `HTTPException` or return a redirect. API routes (JSON) would get a 403; page routes would redirect to the upload page.

```python
def get_data_loader() -> DataLoader:
    if not app_state.is_loaded:
        raise HTTPException(status_code=403, detail="No data loaded")
    return app_state.loader
```

**Option B: Middleware**

A middleware that intercepts all requests except `/upload` and `/static` and redirects to the upload page if no data is loaded. Simpler to implement and covers all routes automatically.

```python
@app.middleware("http")
async def require_data(request: Request, call_next):
    allowed = ("/upload", "/static", "/api/upload")
    if not app_state.is_loaded and not any(request.url.path.startswith(p) for p in allowed):
        return RedirectResponse(url="/upload")
    return await call_next(request)
```

Option B is recommended — it's a single check that covers everything and keeps route handlers unchanged.

### 4. Upload page

A new template (`upload.html`) shown when no data is loaded. Needs:

- File input accepting `.zip` files
- A submit button
- Error display area (invalid file, missing expected JSON files, etc.)
- Brief instructions ("Download your data from Spotify privacy settings, then upload the zip file here")

This becomes the effective landing page until data is provided.

### 5. Reset mechanism

Add a reset endpoint and a button in the UI (e.g. in the nav bar):

```
POST /api/reset
```

This calls `app_state.reset()`, cleans up the temporary directory, and redirects to the upload page. The button should have a confirmation step to prevent accidental resets.

### 6. Temporary file cleanup

Extracted zip contents go into a `tempfile.mkdtemp()` directory. Cleanup should happen:

- On reset (before creating new state)
- On new upload (replace previous data)
- Optionally on app shutdown (register an `atexit` handler or FastAPI lifespan event)

Store the temp directory path in `AppState` so it can be cleaned up:

```python
class AppState:
    def __init__(self):
        self.loader: DataLoader | None = None
        self._temp_dir: Path | None = None

    def load_from_directory(self, data_dir: Path):
        self._cleanup_temp()
        self._temp_dir = data_dir
        self.loader = DataLoader(data_dir)

    def reset(self):
        self._cleanup_temp()
        self.loader = None

    def _cleanup_temp(self):
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
            self._temp_dir = None
```

### 7. Zip validation

Before extracting, validate:

- File is a valid zip archive (`zipfile.is_zipfile()`)
- Contains at least `Playlist1.json.json` (the minimum required file)
- File size is within a reasonable limit (Spotify exports are typically under 10MB; set a 50MB cap)
- No path traversal in zip entries (`..` in filenames — use `zipfile.Path` or sanitise)

Return clear error messages for each failure case.

## Changes Required

| File | Change |
|---|---|
| `main.py` | Replace global `DataLoader` with `AppState`; add middleware; add upload/reset routes; add lifespan cleanup |
| `src/loaders.py` | No changes needed — already accepts a `Path` argument |
| `src/api/*.py` | Update `get_data_loader` import (or no change if middleware handles gating) |
| `src/templates/upload.html` | New template for the upload page |
| `src/templates/base.html` | Add reset button to nav bar |
| `tests/` | New tests for upload, reset, and gating behaviour |

## Things This Design Intentionally Avoids

- **Multi-user support / sessions**: This is a single-user local tool. Server-side sessions, databases, or user auth would be over-engineering.
- **Persistent storage**: Data lives in memory and a temp directory for the duration of use. There's no need to save state between server restarts.
- **Background processing**: Spotify exports are small (a few MB). Extraction and parsing will complete within a normal request cycle — no need for async task queues.
- **Streaming upload / chunked processing**: Same reasoning. The files are small enough to handle in one go.
