# Lab Book - Spotify Data Tool Development

## Date: 2026-01-07

### Phase 1: Project Setup & Dependencies

#### Initial State Assessment
- **pyproject.toml**: Currently minimal, empty dependencies array
- **Python version**: >=3.13 (good, modern version)
- **Project structure**: Very basic, just main.py currently

#### Task 1: Read current pyproject.toml
**Status**: ✅ Complete

**Findings**:
- Project name: spotify-data-tool
- Version: 0.1.0
- No dependencies currently defined
- Ready to add FastAPI stack

**Next Steps**: Add dependencies for web application approach

---

#### Task 2: Update pyproject.toml with dependencies
**Status**: ✅ Complete

**Dependencies added**:
- fastapi>=0.109.0 (main web framework)
- uvicorn[standard]>=0.27.0 (ASGI server)
- jinja2>=3.1.0 (templating engine)
- python-multipart>=0.0.6 (for form handling, useful for future file uploads)

**Rationale**:
- FastAPI: Modern, fast, with automatic API docs
- Uvicorn: Production-ready ASGI server with auto-reload for development
- Jinja2: Template engine for HTML rendering
- python-multipart: Standard addition for web apps, supports form data

---

#### Task 3: Create project directory structure
**Status**: ✅ Complete

**Directories created**:
```
src/
├── __init__.py
├── models.py
├── loaders.py
├── analytics.py
├── api/
│   ├── __init__.py
│   ├── playlists.py
│   ├── tracks.py
│   └── analytics.py
└── templates/
    ├── base.html
    ├── index.html
    ├── playlists.html
    ├── tracks.html
    └── analytics.html

static/
├── css/
│   └── custom.css
└── js/
    └── app.js

tests/
└── __init__.py
```

**Notes**:
- All necessary directories created successfully
- Python package structure with __init__.py files
- Separate folders for templates and static assets
- Tests folder prepared for future test development

---

#### Task 4: Install dependencies with uv
**Status**: ✅ Complete

**Process**:
1. Initial attempt with `uv pip install -e .` failed - no virtual environment found
2. User suggested using `uv sync` instead
3. `uv sync` successfully:
   - Created virtual environment at `.venv`
   - Resolved 24 packages
   - Installed 22 packages in 36ms

**Installed packages (key ones)**:
- fastapi==0.128.0 (✅ meets >=0.109.0 requirement)
- uvicorn==0.40.0 (✅ meets >=0.27.0 requirement)
- jinja2==3.1.6 (✅ meets >=3.1.0 requirement)
- python-multipart==0.0.21 (✅ meets >=0.0.6 requirement)

**Additional dependencies installed automatically**:
- pydantic==2.12.5 & pydantic-core==2.41.5 (for data validation)
- starlette==0.50.0 (FastAPI is built on Starlette)
- uvloop==0.22.1 (high-performance event loop)
- watchfiles==1.1.1 (for auto-reload during development)
- websockets==15.0.1 (WebSocket support)
- httptools==0.7.1 (HTTP parsing)

**Key Learning**:
- `uv sync` is the modern way to set up a project with uv
- It handles virtual environment creation + dependency installation in one command
- Much cleaner than the older `uv venv` + `uv pip install` workflow

---

### Phase 1 Summary

**Status**: ✅ COMPLETE

**Time Taken**: ~10 minutes (faster than estimated 30-45 minutes)

**Deliverables Completed**:
- ✅ Updated pyproject.toml with all required dependencies
- ✅ Complete directory structure created
- ✅ All dependencies installed and verified
- ✅ Virtual environment set up at .venv

**Ready for Phase 2**: Core Data Models & Loading

**Notes for Next Phase**:
- All Python files are currently empty and ready for implementation
- Need to implement Pydantic models for Track, Playlist, etc.
- Need to create DataLoader class with caching
- Data files are already present in `data/` directory

---

## Phase 2: Core Data Models & Loading

**Started**: 2026-01-07

### How I'm Feeling
😊 **Excited and confident!** Phase 1 went smoothly, and now I'm diving into the actual data modeling. I love this part - understanding the data structure and creating clean abstractions. Looking at the real Spotify data files is satisfying because I can see exactly what we're working with.

🤔 **Slightly cautious** - The data files have some complexity (track vs episode vs audiobook in playlist items, nullable fields). Need to handle these edge cases properly with Optional types.

### Task 1: Examine data file structure
**Status**: ✅ Complete

**Data Structures Discovered**:

1. **Playlist1.json.json** structure:
   - Root: `{ "playlists": [...] }`
   - Each playlist has: name, lastModifiedDate, collaborators, items
   - Each item can contain: track, episode, audiobook, or localTrack (all nullable!)
   - Track structure: trackName, artistName, albumName, trackUri
   - Each item also has: addedDate

2. **StreamingHistory_music_0.json.json** structure:
   - Root: Array of streaming events `[...]`
   - Each event: endTime, artistName, trackName, msPlayed
   - Simple flat structure, no nesting

3. **YourLibrary.json.json** structure:
   - Root: `{ "tracks": [...] }`
   - Each track: artist, album, track, uri
   - Different field names than playlist tracks! (track vs trackName, artist vs artistName)

**Key Observations**:
- ⚠️ Field naming inconsistency between files (track vs trackName, artist vs artistName)
- ⚠️ Playlist items can be null (need Optional types)
- ⚠️ Multiple media types in playlists (track, episode, audiobook, localTrack)
- ✅ All tracks have URI for unique identification
- ✅ Data is clean and well-structured overall

**Feeling**: 😌 Relieved that the data is mostly well-structured. The inconsistencies are manageable.

---

### Task 2: Create Pydantic models
**Status**: ✅ Complete

**Models Created**:
1. **Playlist Models**:
   - `PlaylistTrack` - Track in a playlist (with field aliases for camelCase)
   - `PlaylistItem` - Container that can hold track/episode/audiobook/localTrack
   - `Playlist` - Full playlist with metadata and items
   - `PlaylistsData` - Root container for all playlists

2. **Streaming History Models**:
   - `StreamingEvent` - Single listening event with helper properties (seconds_played, minutes_played)

3. **Library Models**:
   - `LibraryTrack` - Track from saved library
   - `LibraryData` - Root container for library tracks

4. **API Response Models**:
   - `PlaylistSummary`, `TrackInfo`, `TopTrackByPlaylist`, `TopTrackByPlays`, `AnalyticsOverview`
   - These will be used for FastAPI endpoint responses

**Key Decisions**:
- Used Pydantic `Field(alias=...)` to handle camelCase JSON keys (trackName → track_name)
- Set `populate_by_name = True` in Config to allow both naming styles
- Made optional fields actually Optional (track, episode, audiobook can be null)
- Added helper properties to StreamingEvent for time conversions

**Feeling**: 🎯 **Focused and methodical**. Pydantic makes this so clean! Love how it handles validation and type conversion automatically.

---

### Task 3: Implement DataLoader class
**Status**: ✅ Complete

**Implementation Details**:
- Singleton-like caching with internal `_cache` dictionary
- Separate methods for validated (Pydantic) and raw (dict) data loading
- Automatic discovery of multiple streaming history files using glob
- Comprehensive error handling with clear error messages
- Cache management utilities (clear_cache, get_cache_keys)

**Methods Implemented**:
- `load_playlists()` / `load_playlists_raw()`
- `load_streaming_history()` / `load_streaming_history_raw()`
- `load_library()` / `load_library_raw()`
- `clear_cache()`, `get_cache_keys()`

**Feeling**: 💪 **Confident and proud**. This is solid, production-ready code with proper error handling and documentation.

---

### Task 4: Test data loading with actual files
**Status**: ✅ Complete

**Test Results** (from test_loader_manual.py):
```
✅ Loaded 178 playlists
✅ Loaded 2520 streaming events
✅ Loaded 2712 saved tracks
✅ Caching works correctly
```

**Key Stats Discovered**:
- Total playlists: 178 (impressive collection!)
- Total streaming events: 2,520
- Total library tracks: 2,712
- First playlist: "ESDS Social - 13.11.2025" with 18 tracks
- First track loaded successfully: "Blues in the News" by Lionel Hampton 🎺

**Feelings**: 🎉 **Thrilled and relieved!** The moment of truth when you run real data through your code and it just... works! No JSON parsing errors, no Pydantic validation failures, everything loaded perfectly on first try. This is such a good feeling!

😊 **Satisfied** - The abstractions are working well. Pydantic caught all the field mappings correctly.

---

### Task 5: Write unit tests
**Status**: ✅ Complete

**Tests Written**: 15 comprehensive unit tests in `tests/test_loaders.py`

**Test Coverage**:
- DataLoader initialization (with Path and string, error handling)
- Loading all data types (playlists, streaming history, library)
- Both validated (Pydantic) and raw (dict) loading methods
- Caching behavior (specific key and all keys)
- Data structure validation
- Time conversion helpers on StreamingEvent
- Data integrity checks

**Test Results**:
```
✅ 15 passed in 0.22s
⚠️  4 deprecation warnings (Pydantic Config class → ConfigDict)
```

**Feelings**: 🏆 **Triumphant!** All tests passed on the first run! This is the developer's dream - you write code, write tests, and everything just works. The test coverage is comprehensive and gives me confidence that the data loading is solid.

🤓 **Slightly perfectionist** - Those deprecation warnings are bothering me. I should fix them to use the modern ConfigDict pattern.

---

### Task 6: Fix Pydantic deprecation warnings
**Status**: ✅ Complete

**Changes Made**:
- Updated all Pydantic models from old `class Config:` to modern `model_config = ConfigDict()`
- Imported `ConfigDict` from pydantic
- Updated 4 models: PlaylistTrack, PlaylistItem, Playlist, StreamingEvent

**Test Results After Fix**:
```
✅ 15 passed in 0.22s
✅ ZERO warnings!
```

**Feeling**: 😌 **Satisfied and at peace**. Those warnings were like a small pebble in my shoe - not a big problem, but annoying. Now they're gone and the code is using the modern Pydantic V2 patterns. Clean, future-proof code feels good!

---

## Phase 2 Summary

**Status**: ✅ COMPLETE

**Time Taken**: ~45 minutes (estimated 2-3 hours, came in WAY under!)

**Deliverables Completed**:
- ✅ Comprehensive Pydantic models for all data types
- ✅ DataLoader class with caching and error handling
- ✅ Successfully loaded 178 playlists, 2520 streaming events, 2712 library tracks
- ✅ 15 passing unit tests with 100% success rate
- ✅ Zero warnings, modern Pydantic V2 code

**Key Achievements**:
- Clean separation between validated (Pydantic) and raw (dict) data access
- Helper properties on StreamingEvent for time conversions
- Comprehensive error handling
- Automatic discovery of multiple streaming history files
- Cache management utilities

**Overall Feeling**: 🎊 **Ecstatic!** Phase 2 went incredibly smoothly. Everything worked on the first try, tests passed immediately, and we even had time to clean up deprecation warnings. This is what good software development feels like - solid abstractions, comprehensive tests, and clean code. Ready for Phase 3!

**Files Created/Modified**:
- ✅ src/models.py (137 lines)
- ✅ src/loaders.py (214 lines)
- ✅ tests/test_loaders.py (221 lines)
- ✅ test_loader_manual.py (temporary test file)
- ✅ pyproject.toml (added pytest dev dependency)

**Ready for Phase 3**: Analytics Engine

---
