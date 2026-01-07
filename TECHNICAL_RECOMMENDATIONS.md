# Technical Recommendations

## Overview
This document outlines different approaches for implementing the Spotify Data Tool based on requirements in README.md and findings in NOTES.md.

## Core Requirements Summary
1. Introspect all playlists (view playlist data)
2. Introspect tracks (view track information)
3. Analytics overview:
   - Most common track across playlists
   - Most played track from streaming history

## Key Technical Challenges
- JSON parsing for large files (1.8MB Playlist1.json.json, 501KB YourLibrary.json.json)
- Track matching across different data sources (URI-based vs name-based)
- String normalization for accurate track matching
- Performance when processing ~60k playlist items and ~12.6k streaming events

---

## Approach 1: Interactive Terminal UI (TUI) with Textual

### Overview
Build an interactive terminal-based application with a rich user interface using Python's Textual framework.

### Technology Stack
- **Framework**: [Textual](https://textual.textualize.io/) - Modern TUI framework
- **Data Processing**: Standard library `json` module
- **Additional Libraries**:
  - `rich` (comes with Textual) - Beautiful terminal output
  - `thefuzz` - Fuzzy string matching for track name matching

### Architecture
```
spotify-data-tool/
├── main.py                    # Entry point with Textual app
├── src/
│   ├── __init__.py
│   ├── models.py             # Data models (Track, Playlist, etc.)
│   ├── loaders.py            # JSON file loading logic
│   ├── analyzers.py          # Analytics calculations
│   ├── matchers.py           # Track matching logic
│   └── ui/
│       ├── __init__.py
│       ├── playlist_view.py  # Playlist browser widget
│       ├── track_view.py     # Track browser widget
│       └── analytics_view.py # Analytics dashboard widget
├── data/                      # User's Spotify data
└── tests/
```

### Implementation Strategy

**Data Loading with Caching:**
```python
class DataLoader:
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._cache = {}

    def load_playlists(self) -> dict:
        if 'playlists' not in self._cache:
            with open(self._data_dir / 'Playlist1.json.json') as f:
                self._cache['playlists'] = json.load(f)
        return self._cache['playlists']
```

**Track Matching Logic:**
```python
def normalize_track_key(track_name: str, artist_name: str) -> str:
    """Create normalized composite key for matching"""
    return f"{track_name.lower().strip()}||{artist_name.lower().strip()}"

def build_track_index(playlists_data):
    """Map normalized keys to track URIs"""
    index = {}
    for playlist in playlists_data['playlists']:
        for item in playlist['items']:
            if item['track']:
                key = normalize_track_key(
                    item['track']['trackName'],
                    item['track']['artistName']
                )
                index[key] = item['track']['trackUri']
    return index
```

**Analytics Calculations:**
```python
from collections import Counter

def most_common_tracks_by_playlist(playlists_data) -> list:
    """Count track appearances across playlists"""
    track_counter = Counter()

    for playlist in playlists_data['playlists']:
        for item in playlist['items']:
            if item['track']:
                uri = item['track']['trackUri']
                track_counter[uri] += 1

    return track_counter.most_common(20)

def most_played_tracks(streaming_history) -> list:
    """Count plays from streaming history"""
    play_counter = Counter()

    for event in streaming_history:
        key = normalize_track_key(
            event['trackName'],
            event['artistName']
        )
        play_counter[key] += 1

    return play_counter.most_common(20)
```

### Pros
- ✅ Fast to build, no web server needed
- ✅ Excellent user experience with keyboard navigation
- ✅ Works entirely offline
- ✅ Low resource usage
- ✅ Cross-platform (works anywhere Python runs)
- ✅ Textual has built-in widgets for tables, lists, tabs
- ✅ Perfect for personal/single-user tool

### Cons
- ❌ Limited to terminal environment
- ❌ Cannot easily share with non-technical users
- ❌ No data visualization (charts/graphs)

### Dependencies
```toml
[project]
dependencies = [
    "textual>=0.47.0",
    "thefuzz>=0.20.0",
]
```

### Development Commands
```bash
# Run the app
python main.py

# Run with dev mode (hot reload)
textual run --dev main.py

# Run tests
pytest tests/
```

---

## Approach 2: Simple CLI Tool with Typer

### Overview
Build a straightforward command-line interface with subcommands for each feature.

### Technology Stack
- **Framework**: [Typer](https://typer.tiangolo.com/) - Modern CLI framework with type hints
- **Output Formatting**: [Rich](https://rich.readthedocs.io/) - Beautiful terminal tables and output
- **Data Processing**: Standard library `json` + `dataclasses`

### Architecture
```
spotify-data-tool/
├── main.py                    # CLI entry point
├── src/
│   ├── __init__.py
│   ├── models.py             # Dataclasses for Track, Playlist
│   ├── loaders.py            # JSON loading
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── playlists.py      # Playlist commands
│   │   ├── tracks.py         # Track commands
│   │   └── analytics.py      # Analytics commands
│   └── utils/
│       ├── matching.py       # Track matching utilities
│       └── formatting.py     # Output formatting
└── tests/
```

### Implementation Strategy

**CLI Structure:**
```python
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

@app.command()
def playlists(
    limit: int = typer.Option(None, help="Limit number of playlists shown"),
    detailed: bool = typer.Option(False, help="Show detailed track listings")
):
    """List all playlists"""
    data = load_playlists()

    table = Table(title="Playlists")
    table.add_column("Name", style="cyan")
    table.add_column("Tracks", justify="right", style="green")
    table.add_column("Last Modified", style="yellow")

    for playlist in data['playlists'][:limit]:
        table.add_row(
            playlist['name'],
            str(len(playlist['items'])),
            playlist['lastModifiedDate']
        )

    console.print(table)

@app.command()
def analytics():
    """Show analytics overview"""
    console.print("[bold]Analytics Overview[/bold]\n")

    # Most common by playlist
    console.print("[cyan]Most Common Tracks (by playlist appearance):[/cyan]")
    show_top_tracks_by_playlist()

    console.print("\n[cyan]Most Played Tracks (by play count):[/cyan]")
    show_most_played_tracks()

if __name__ == "__main__":
    app()
```

**Usage Examples:**
```bash
# List all playlists
python main.py playlists

# List playlists with details
python main.py playlists --detailed

# Show only first 10 playlists
python main.py playlists --limit 10

# Show analytics
python main.py analytics

# Show track info
python main.py tracks --search "fela kuti"

# Export analytics to JSON
python main.py analytics --export output.json
```

### Pros
- ✅ Very simple to implement
- ✅ Easy to script and automate
- ✅ Minimal dependencies
- ✅ Great for power users
- ✅ Can pipe output to other tools
- ✅ Fast execution

### Cons
- ❌ Less interactive than TUI
- ❌ Requires running separate commands for each action
- ❌ Less visually appealing
- ❌ Harder for non-technical users

### Dependencies
```toml
[project]
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
]
```

---

## Approach 3: Web Application with Dashboard

### Overview
Build a web application with an interactive dashboard for visualizing and exploring the data.

### Technology Stack
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) - Modern async web framework
- **Frontend**: [HTMX](https://htmx.org/) + [Alpine.js](https://alpinejs.dev/) - Minimal JS framework
- **Templating**: [Jinja2](https://jinja.palletsprojects.com/) (comes with FastAPI)
- **Charts**: [Chart.js](https://www.chartjs.org/) via CDN
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) via CDN

### Architecture
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
│   └── js/
└── data/
```

### Implementation Strategy

**Backend API:**
```python
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="src/templates")

# Singleton data loader with caching
data_loader = DataLoader(Path("data"))

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/playlists")
async def get_playlists(limit: int = None) -> List[dict]:
    """Get all playlists"""
    playlists = data_loader.load_playlists()['playlists']
    if limit:
        playlists = playlists[:limit]
    return [
        {
            "name": p['name'],
            "track_count": len(p['items']),
            "last_modified": p['lastModifiedDate']
        }
        for p in playlists
    ]

@app.get("/api/analytics/top-tracks-by-playlist")
async def top_tracks_playlist() -> List[dict]:
    """Get most common tracks across playlists"""
    playlists = data_loader.load_playlists()
    results = calculate_top_tracks_by_playlist(playlists)
    return results

@app.get("/api/analytics/top-tracks-by-plays")
async def top_tracks_plays() -> List[dict]:
    """Get most played tracks"""
    history = data_loader.load_streaming_history()
    results = calculate_most_played(history)
    return results
```

**Frontend (HTMX + Alpine.js):**
```html
<!-- templates/analytics.html -->
<div class="container mx-auto p-8">
    <h1 class="text-3xl font-bold mb-8">Analytics Dashboard</h1>

    <!-- Most Common by Playlist -->
    <div class="bg-white shadow rounded-lg p-6 mb-8">
        <h2 class="text-xl font-semibold mb-4">Most Common Tracks (by playlist)</h2>
        <div hx-get="/api/analytics/top-tracks-by-playlist"
             hx-trigger="load"
             hx-target="#playlist-chart-container">
            Loading...
        </div>
        <canvas id="playlist-chart"></canvas>
    </div>

    <!-- Most Played -->
    <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-xl font-semibold mb-4">Most Played Tracks</h2>
        <div hx-get="/api/analytics/top-tracks-by-plays"
             hx-trigger="load"
             hx-target="#plays-chart-container">
            Loading...
        </div>
        <canvas id="plays-chart"></canvas>
    </div>
</div>

<script>
// Chart.js integration
fetch('/api/analytics/top-tracks-by-playlist')
    .then(res => res.json())
    .then(data => {
        new Chart(document.getElementById('playlist-chart'), {
            type: 'bar',
            data: {
                labels: data.map(d => d.track_name),
                datasets: [{
                    label: 'Playlist Count',
                    data: data.map(d => d.count),
                    backgroundColor: 'rgba(54, 162, 235, 0.6)'
                }]
            }
        });
    });
</script>
```

### Pros
- ✅ Best visual presentation with charts/graphs
- ✅ Accessible from any device with browser
- ✅ Can add complex filtering and search
- ✅ Easy to share (run locally, show others)
- ✅ Modern, polished UI
- ✅ Can add export features (CSV, JSON, etc.)
- ✅ Future-proof for additional features

### Cons
- ❌ More complex to build
- ❌ Requires running web server
- ❌ More dependencies
- ❌ Slower initial load time (parsing large JSON files)
- ❌ Need to think about caching strategy

### Dependencies
```toml
[project]
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "jinja2>=3.1.0",
]
```

### Development Commands
```bash
# Run development server
uvicorn main:app --reload --port 8000

# Access at http://localhost:8000
```

---

## Approach 4: Data Analysis with Pandas

### Overview
Use pandas for data manipulation with either Jupyter notebooks or simple Python scripts for quick analysis.

### Technology Stack
- **Core**: pandas, numpy
- **Visualization**: matplotlib, seaborn, plotly
- **Interface**: Jupyter Notebook or Python script

### Architecture
```
spotify-data-tool/
├── main.py                    # Script entry point
├── notebooks/
│   ├── exploration.ipynb     # Data exploration
│   └── analytics.ipynb       # Analytics report
├── src/
│   ├── __init__.py
│   ├── loaders.py           # Reusable loading functions
│   └── analytics.py         # Reusable analytics functions
└── data/
```

### Implementation Strategy

**Data Loading:**
```python
import pandas as pd
import json

# Load and flatten playlist data
with open('data/Playlist1.json.json') as f:
    playlists_data = json.load(f)

playlist_tracks = []
for playlist in playlists_data['playlists']:
    for item in playlist['items']:
        if item['track']:
            playlist_tracks.append({
                'playlist_name': playlist['name'],
                'track_name': item['track']['trackName'],
                'artist_name': item['track']['artistName'],
                'track_uri': item['track']['trackUri'],
                'added_date': item['addedDate']
            })

df_playlists = pd.DataFrame(playlist_tracks)

# Load streaming history
with open('data/StreamingHistory_music_0.json.json') as f:
    streaming_data = json.load(f)
df_streaming = pd.DataFrame(streaming_data)
```

**Analytics:**
```python
# Most common tracks by playlist
track_playlist_counts = df_playlists.groupby(['track_name', 'artist_name']).size()
top_tracks = track_playlist_counts.nlargest(20)

# Most played tracks
play_counts = df_streaming.groupby(['trackName', 'artistName']).size()
top_played = play_counts.nlargest(20)

# Visualization
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 8))
top_tracks.plot(kind='barh')
plt.xlabel('Number of Playlists')
plt.title('Top 20 Tracks by Playlist Appearance')
plt.tight_layout()
plt.show()
```

### Pros
- ✅ Fastest to prototype
- ✅ Interactive exploration
- ✅ pandas provides powerful data manipulation
- ✅ Rich visualization options
- ✅ Great for one-off analyses
- ✅ Can export to HTML for sharing

### Cons
- ❌ Not a standalone tool
- ❌ Requires Jupyter environment
- ❌ Less polished for end users
- ❌ Manual cell execution required
- ❌ Not suitable for repeated use by non-technical users

### Dependencies
```toml
[project]
dependencies = [
    "pandas>=2.0.0",
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
    "jupyter>=1.0.0",
]
```

---

## Comparison Matrix

| Feature | TUI (Textual) | CLI (Typer) | Web (FastAPI) | Pandas |
|---------|---------------|-------------|---------------|---------|
| **Development Time** | Medium | Fast | Slow | Very Fast |
| **User Experience** | Excellent | Good | Excellent | Fair |
| **Interactivity** | High | Low | High | High |
| **Visual Appeal** | Good | Basic | Excellent | Good |
| **Performance** | Excellent | Excellent | Good | Good |
| **Easy to Share** | Medium | Easy | Easy | Hard |
| **Maintenance** | Medium | Low | High | Low |
| **Best For** | Personal tool | Power users | Sharing/Demo | Quick analysis |

---

## Recommendation

### Primary: **Approach 1 (TUI with Textual)** ✨

**Reasoning:**
1. **Right balance** - Interactive UX with reasonable development time
2. **No server overhead** - Runs directly, no web server management
3. **Personal tool focus** - Based on README ("She wants to..."), this appears to be a personal/gift project
4. **Offline-first** - All data stays local, no security concerns
5. **Professional feel** - Textual provides beautiful, modern terminal UI
6. **Extensible** - Easy to add new views/features

### Alternative: **Approach 3 (Web Dashboard)**
If the goal is to demo or share with others who may not be technical, the web dashboard provides the best visual presentation.

### Alternative: **Approach 4 (Pandas)**
If this is just for quick one-time analysis and the user is comfortable with Python/Jupyter, pandas is fastest to results.

---

## Implementation Plan (for TUI approach)

### Phase 1: Core Data Loading (2-3 hours)
- Set up project structure
- Implement JSON loaders for 3 main files
- Create data models
- Write unit tests for loading

### Phase 2: Analytics Logic (2-3 hours)
- Implement track matching logic
- Calculate most common tracks (playlist)
- Calculate most played tracks (streaming)
- Test with actual data

### Phase 3: TUI Interface (3-4 hours)
- Create Textual app skeleton
- Build playlist browser view
- Build track browser view
- Build analytics dashboard view
- Add navigation between views

### Phase 4: Polish (1-2 hours)
- Add keyboard shortcuts
- Improve formatting
- Add help screen
- Error handling

**Total Estimated Time:** 8-12 hours for full implementation
