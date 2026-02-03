# Implementation Plan: Approach 3 - Web Application with Dashboard

## Project Overview
Building a web application with FastAPI backend and HTMX/Alpine.js frontend to visualize and explore Spotify data with interactive charts and dashboards.

---

## Phase 1: Project Setup & Dependencies
**Estimated Time: 30-45 minutes**

### Tasks
1. **Update pyproject.toml with dependencies**
   - Add FastAPI (>=0.109.0)
   - Add uvicorn[standard] (>=0.27.0)
   - Add Jinja2 (>=3.1.0)
   - Add python-multipart for form handling

2. **Create project structure**
   ```
   spotify-data-tool/
   ├── main.py                    # FastAPI app entry
   ├── src/
   │   ├── __init__.py
   │   ├── models.py             # Pydantic models
   │   ├── loaders.py            # Data loading with caching
   │   ├── analytics.py          # Analytics calculations
   │   ├── api/
   │   │   ├── __init__.py
   │   │   ├── playlists.py      # Playlist endpoints
   │   │   ├── tracks.py         # Track endpoints
   │   │   └── analytics.py      # Analytics endpoints
   │   └── templates/
   │       ├── base.html
   │       ├── index.html
   │       ├── playlists.html
   │       ├── tracks.html
   │       └── analytics.html
   ├── static/
   │   ├── css/
   │   │   └── custom.css
   │   └── js/
   │       └── app.js
   └── data/
   ```

3. **Install dependencies**
   ```bash
   uv pip install -e .
   ```

### Deliverables
- Updated pyproject.toml
- Complete directory structure
- All dependencies installed

---

## Phase 2: Core Data Models & Loading
**Estimated Time: 2-3 hours**

### Tasks

1. **Create Pydantic models (src/models.py)**
   - `Track` model (trackUri, trackName, artistName, albumName, etc.)
   - `PlaylistItem` model (track, addedDate)
   - `Playlist` model (name, items, lastModifiedDate)
   - `StreamingEvent` model (trackName, artistName, msPlayed, endTime)
   - Response models for API endpoints

2. **Implement data loader with caching (src/loaders.py)**
   - `DataLoader` class with singleton pattern
   - `load_playlists()` - Load Playlist1.json.json
   - `load_library()` - Load YourLibrary.json.json
   - `load_streaming_history()` - Load StreamingHistory files
   - In-memory caching to avoid re-parsing large JSON files
   - Error handling for missing/corrupted files

3. **Write unit tests (tests/test_loaders.py)**
   - Test successful data loading
   - Test caching behavior
   - Test error handling

### Code Samples

**src/models.py:**
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Track(BaseModel):
    track_uri: str = Field(alias="trackUri")
    track_name: str = Field(alias="trackName")
    artist_name: str = Field(alias="artistName")
    album_name: str = Field(alias="albumName")

    class Config:
        populate_by_name = True

class PlaylistItem(BaseModel):
    track: Optional[Track]
    added_date: str = Field(alias="addedDate")

class Playlist(BaseModel):
    name: str
    items: List[PlaylistItem]
    last_modified_date: str = Field(alias="lastModifiedDate")
```

**src/loaders.py:**
```python
import json
from pathlib import Path
from typing import Dict, List
from functools import lru_cache

class DataLoader:
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._cache: Dict = {}

    def load_playlists(self) -> dict:
        if 'playlists' not in self._cache:
            with open(self._data_dir / 'Playlist1.json.json') as f:
                self._cache['playlists'] = json.load(f)
        return self._cache['playlists']

    def load_streaming_history(self) -> List[dict]:
        if 'streaming' not in self._cache:
            history = []
            for file in self._data_dir.glob('StreamingHistory_music_*.json.json'):
                with open(file) as f:
                    history.extend(json.load(f))
            self._cache['streaming'] = history
        return self._cache['streaming']

    def load_library(self) -> dict:
        if 'library' not in self._cache:
            with open(self._data_dir / 'YourLibrary.json.json') as f:
                self._cache['library'] = json.load(f)
        return self._cache['library']
```

### Deliverables
- Complete Pydantic models
- Working DataLoader with caching
- Unit tests passing

---

## Phase 3: Analytics Engine
**Estimated Time: 2-3 hours**

### Tasks

1. **Implement track matching utilities (src/analytics.py)**
   - `normalize_track_key()` - Create normalized composite key
   - `build_track_index()` - Map normalized keys to URIs
   - Handle case sensitivity, whitespace, special characters

2. **Implement analytics calculations (src/analytics.py)**
   - `calculate_most_common_tracks_by_playlist()` - Count track appearances across playlists
   - `calculate_most_played_tracks()` - Count plays from streaming history
   - `calculate_playlist_statistics()` - Total tracks, unique tracks, etc.
   - `match_streaming_to_playlists()` - Link streaming history to playlist tracks

3. **Performance optimization**
   - Use Counter for efficient counting
   - Index building for fast lookups
   - Lazy loading where possible

4. **Write unit tests (tests/test_analytics.py)**
   - Test track normalization
   - Test analytics calculations with sample data
   - Test edge cases (empty playlists, missing data)

### Code Samples

**src/analytics.py:**
```python
from collections import Counter
from typing import List, Dict, Tuple

def normalize_track_key(track_name: str, artist_name: str) -> str:
    """Create normalized composite key for matching"""
    track = track_name.lower().strip()
    artist = artist_name.lower().strip()
    return f"{track}||{artist}"

def calculate_most_common_tracks_by_playlist(playlists_data: dict, top_n: int = 20) -> List[Dict]:
    """Count track appearances across playlists"""
    track_counter = Counter()
    track_info = {}

    for playlist in playlists_data['playlists']:
        for item in playlist['items']:
            if item['track']:
                uri = item['track']['trackUri']
                track_counter[uri] += 1

                # Store track info for display
                if uri not in track_info:
                    track_info[uri] = {
                        'name': item['track']['trackName'],
                        'artist': item['track']['artistName']
                    }

    results = []
    for uri, count in track_counter.most_common(top_n):
        results.append({
            'track_uri': uri,
            'track_name': track_info[uri]['name'],
            'artist_name': track_info[uri]['artist'],
            'playlist_count': count
        })

    return results

def calculate_most_played_tracks(streaming_history: List[dict], top_n: int = 20) -> List[Dict]:
    """Count plays from streaming history"""
    play_counter = Counter()

    for event in streaming_history:
        key = normalize_track_key(
            event['trackName'],
            event['artistName']
        )
        play_counter[key] += 1

    results = []
    for key, count in play_counter.most_common(top_n):
        track_name, artist_name = key.split('||')
        results.append({
            'track_name': track_name.title(),
            'artist_name': artist_name.title(),
            'play_count': count
        })

    return results
```

### Deliverables
- Complete analytics module
- Track matching utilities
- Unit tests passing
- Verified results with actual data

---

## Phase 4: FastAPI Backend - Core Routes
**Estimated Time: 2-3 hours**

### Tasks

1. **Create FastAPI app skeleton (main.py)**
   - Initialize FastAPI app
   - Mount static files
   - Configure Jinja2 templates
   - Create singleton DataLoader instance
   - Add CORS middleware if needed

2. **Implement base routes (main.py)**
   - `GET /` - Serve index/dashboard page
   - `GET /playlists` - Serve playlists page
   - `GET /tracks` - Serve tracks page
   - `GET /analytics` - Serve analytics page

3. **Implement API endpoints (src/api/)**
   - **playlists.py:**
     - `GET /api/playlists` - List all playlists
     - `GET /api/playlists/{name}` - Get specific playlist with tracks
   - **tracks.py:**
     - `GET /api/tracks` - Search/filter tracks
     - `GET /api/tracks/{uri}` - Get track details
   - **analytics.py:**
     - `GET /api/analytics/top-tracks-by-playlist` - Most common tracks
     - `GET /api/analytics/top-tracks-by-plays` - Most played tracks
     - `GET /api/analytics/overview` - General statistics

4. **Add error handling**
   - Custom exception handlers
   - 404 for missing resources
   - 500 for server errors

### Code Samples

**main.py:**
```python
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

from src.loaders import DataLoader
from src.api import playlists, tracks, analytics

app = FastAPI(title="Spotify Data Tool")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="src/templates")

# Singleton data loader
data_loader = DataLoader(Path("data"))

# Include API routers
app.include_router(playlists.router, prefix="/api/playlists", tags=["playlists"])
app.include_router(tracks.router, prefix="/api/tracks", tags=["tracks"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/playlists", response_class=HTMLResponse)
async def playlists_page(request: Request):
    return templates.TemplateResponse("playlists.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

**src/api/analytics.py:**
```python
from fastapi import APIRouter, Depends
from typing import List
from pathlib import Path

from src.loaders import DataLoader
from src.analytics import (
    calculate_most_common_tracks_by_playlist,
    calculate_most_played_tracks
)

router = APIRouter()

def get_data_loader():
    return DataLoader(Path("data"))

@router.get("/top-tracks-by-playlist")
async def top_tracks_by_playlist(
    limit: int = 20,
    loader: DataLoader = Depends(get_data_loader)
) -> List[dict]:
    """Get most common tracks across playlists"""
    playlists = loader.load_playlists()
    return calculate_most_common_tracks_by_playlist(playlists, top_n=limit)

@router.get("/top-tracks-by-plays")
async def top_tracks_by_plays(
    limit: int = 20,
    loader: DataLoader = Depends(get_data_loader)
) -> List[dict]:
    """Get most played tracks from streaming history"""
    history = loader.load_streaming_history()
    return calculate_most_played_tracks(history, top_n=limit)

@router.get("/overview")
async def analytics_overview(loader: DataLoader = Depends(get_data_loader)) -> dict:
    """Get general statistics"""
    playlists = loader.load_playlists()
    history = loader.load_streaming_history()

    total_playlists = len(playlists['playlists'])
    total_playlist_items = sum(len(p['items']) for p in playlists['playlists'])
    total_streams = len(history)

    return {
        'total_playlists': total_playlists,
        'total_playlist_items': total_playlist_items,
        'total_streams': total_streams
    }
```

### Deliverables
- Working FastAPI application
- All API endpoints functional
- API documentation at /docs
- Error handling in place

---

## Phase 5: Frontend - Templates & Styling
**Estimated Time: 3-4 hours**

### Tasks

1. **Create base template (src/templates/base.html)**
   - HTML structure with navigation
   - Include Tailwind CSS via CDN
   - Include HTMX via CDN
   - Include Alpine.js via CDN
   - Include Chart.js via CDN
   - Common header/footer

2. **Create page templates**
   - **index.html** - Dashboard/home with overview stats
   - **playlists.html** - Browse all playlists
   - **tracks.html** - Search and view tracks
   - **analytics.html** - Analytics dashboard with charts

3. **Add HTMX interactions**
   - Load data dynamically without page refresh
   - Pagination for playlists
   - Search/filter functionality
   - Modal dialogs for track details

4. **Style with Tailwind CSS**
   - Responsive grid layout
   - Cards for playlists and tracks
   - Tables for data display
   - Loading states

### Code Samples

**src/templates/base.html:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Spotify Data Tool{% endblock %}</title>

    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>

    <!-- Alpine.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>

    <!-- Custom CSS -->
    <link rel="stylesheet" href="{{ url_for('static', path='/css/custom.css') }}">
</head>
<body class="bg-gray-50">
    <!-- Navigation -->
    <nav class="bg-green-600 text-white shadow-lg">
        <div class="container mx-auto px-4 py-4">
            <div class="flex items-center justify-between">
                <h1 class="text-2xl font-bold">Spotify Data Tool</h1>
                <div class="space-x-4">
                    <a href="/" class="hover:underline">Dashboard</a>
                    <a href="/playlists" class="hover:underline">Playlists</a>
                    <a href="/analytics" class="hover:underline">Analytics</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="container mx-auto px-4 py-8">
        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    <footer class="bg-gray-800 text-white text-center py-4 mt-12">
        <p>Spotify Data Tool - Built with FastAPI & HTMX</p>
    </footer>

    {% block scripts %}{% endblock %}
</body>
</html>
```

**src/templates/analytics.html:**
```html
{% extends "base.html" %}

{% block title %}Analytics - Spotify Data Tool{% endblock %}

{% block content %}
<div x-data="analyticsData()">
    <h1 class="text-3xl font-bold mb-8">Analytics Dashboard</h1>

    <!-- Overview Stats -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
         hx-get="/api/analytics/overview"
         hx-trigger="load"
         hx-swap="innerHTML">
        <div class="bg-white rounded-lg shadow p-6">
            <div class="text-gray-500 text-sm">Loading...</div>
        </div>
    </div>

    <!-- Most Common Tracks by Playlist -->
    <div class="bg-white shadow rounded-lg p-6 mb-8">
        <h2 class="text-xl font-semibold mb-4">Most Common Tracks (by playlist appearance)</h2>
        <div class="mb-4">
            <canvas id="playlist-chart" height="80"></canvas>
        </div>
        <div id="playlist-table" class="overflow-x-auto"></div>
    </div>

    <!-- Most Played Tracks -->
    <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-xl font-semibold mb-4">Most Played Tracks (from streaming history)</h2>
        <div class="mb-4">
            <canvas id="plays-chart" height="80"></canvas>
        </div>
        <div id="plays-table" class="overflow-x-auto"></div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
function analyticsData() {
    return {
        init() {
            this.loadCharts();
        },

        async loadCharts() {
            // Load playlist chart
            const playlistData = await fetch('/api/analytics/top-tracks-by-playlist?limit=20')
                .then(res => res.json());

            new Chart(document.getElementById('playlist-chart'), {
                type: 'bar',
                data: {
                    labels: playlistData.map(d => `${d.track_name} - ${d.artist_name}`),
                    datasets: [{
                        label: 'Playlist Count',
                        data: playlistData.map(d => d.playlist_count),
                        backgroundColor: 'rgba(34, 197, 94, 0.6)',
                        borderColor: 'rgba(34, 197, 94, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false }
                    }
                }
            });

            // Load plays chart
            const playsData = await fetch('/api/analytics/top-tracks-by-plays?limit=20')
                .then(res => res.json());

            new Chart(document.getElementById('plays-chart'), {
                type: 'bar',
                data: {
                    labels: playsData.map(d => `${d.track_name} - ${d.artist_name}`),
                    datasets: [{
                        label: 'Play Count',
                        data: playsData.map(d => d.play_count),
                        backgroundColor: 'rgba(59, 130, 246, 0.6)',
                        borderColor: 'rgba(59, 130, 246, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    }
}
</script>
{% endblock %}
```

### Deliverables
- Complete template system
- Responsive, styled pages
- HTMX dynamic loading working
- Charts rendering properly

---

## Phase 6: Interactive Features & Polish
**Estimated Time: 2-3 hours**

### Tasks

1. **Add search and filtering**
   - Search tracks by name/artist
   - Filter playlists by name
   - Pagination for large datasets

2. **Add interactive elements**
   - Click track to see details (modal or sidebar)
   - Sort tables by different columns
   - Toggle between chart types (bar/pie)
   - Export data to CSV/JSON

3. **Performance optimizations**
   - Lazy loading for long lists
   - Virtual scrolling for large tables
   - Debounce search inputs
   - Cache API responses in frontend

4. **Error handling & UX**
   - Loading spinners
   - Error messages
   - Empty state handling
   - Keyboard shortcuts

5. **Add custom styling (static/css/custom.css)**
   - Custom color scheme
   - Animations and transitions
   - Dark mode support (optional)

### Deliverables
- Fully interactive application
- Smooth user experience
- Error handling throughout
- Professional polish

---

## Phase 7: Testing & Documentation
**Estimated Time: 1-2 hours**

### Tasks

1. **Write API tests (tests/test_api.py)**
   - Test all endpoints
   - Test error cases
   - Test data validation

2. **Manual testing checklist**
   - [ ] All pages load correctly
   - [ ] Navigation works
   - [ ] Charts render properly
   - [ ] Search/filter works
   - [ ] Responsive on mobile
   - [ ] Browser compatibility (Chrome, Firefox, Safari)

3. **Update documentation**
   - Update README.md with setup instructions
   - Document API endpoints
   - Add screenshots
   - Document configuration options

4. **Create development guide**
   - How to run locally
   - How to add new features
   - Code structure explanation

### Deliverables
- Comprehensive test suite
- Complete documentation
- Tested application ready for use

---

## Development Commands Reference

```bash
# Install dependencies
uv pip install -e .

# Run development server
uvicorn main:app --reload --port 8000

# Run with custom host/port
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Access application
# http://localhost:8000

# Access API docs
# http://localhost:8000/docs
```

---

## Total Estimated Time
**12-18 hours** for complete implementation

### Time Breakdown by Phase
1. Project Setup: 0.5-0.75 hours
2. Core Data Models: 2-3 hours
3. Analytics Engine: 2-3 hours
4. FastAPI Backend: 2-3 hours
5. Frontend Templates: 3-4 hours
6. Interactive Features: 2-3 hours
7. Testing & Documentation: 1-2 hours

---

## Success Criteria

- ✅ Web server runs without errors
- ✅ All API endpoints return correct data
- ✅ Dashboard displays analytics with charts
- ✅ Playlist browser shows all playlists
- ✅ Search and filtering work correctly
- ✅ Responsive design works on mobile
- ✅ Unit tests pass
- ✅ Documentation is complete
- ✅ Performance is acceptable (<2s page load)

---

## Future Enhancements (Post-MVP)

1. **Advanced Analytics**
   - Listening trends over time
   - Genre analysis
   - Discover patterns in listening habits

2. **Export Features**
   - Export analytics to PDF
   - Export playlists to CSV
   - Generate shareable reports

3. **Playlist Management**
   - Create new playlists from analytics
   - Merge/split playlists
   - Remove duplicates

4. **Authentication** (if sharing publicly)
   - User accounts
   - Multi-user support
   - Secure data storage

5. **Real-time Updates**
   - Watch data directory for changes
   - Auto-refresh dashboard
   - WebSocket support
