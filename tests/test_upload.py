"""Tests for file upload, reset, and gating behaviour."""

import io
import json
import tempfile
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import AppState, app, app_state


@pytest.fixture(autouse=True)
def _reset_state():
    """Ensure app_state is clean before and after each test."""
    app_state.reset()
    yield
    app_state.reset()


@pytest.fixture()
def client():
    return TestClient(app, follow_redirects=False)


def _make_zip(files: dict[str, object]) -> bytes:
    """Create a zip file in memory with the given filename -> content mapping."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, json.dumps(content))
    return buf.getvalue()


MINIMAL_PLAYLISTS = {"playlists": [{"name": "Test", "items": []}]}
MINIMAL_STREAMING = [
    {"endTime": "2024-01-01 12:00", "artistName": "A", "trackName": "T", "msPlayed": 60000}
]


def _valid_zip() -> bytes:
    return _make_zip(
        {
            "Playlist1.json.json": MINIMAL_PLAYLISTS,
            "StreamingHistory_music_0.json.json": MINIMAL_STREAMING,
        }
    )


# ---------------------------------------------------------------------------
# AppState unit tests
# ---------------------------------------------------------------------------


class TestAppState:
    def test_initial_state(self):
        state = AppState()
        assert not state.is_loaded
        assert state.loader is None

    def test_load_from_directory(self, tmp_path):
        playlist_file = tmp_path / "Playlist1.json.json"
        playlist_file.write_text(json.dumps(MINIMAL_PLAYLISTS))

        state = AppState()
        state.load_from_directory(tmp_path)
        assert state.is_loaded
        assert state.loader is not None

    def test_reset_clears_loader(self, tmp_path):
        playlist_file = tmp_path / "Playlist1.json.json"
        playlist_file.write_text(json.dumps(MINIMAL_PLAYLISTS))

        state = AppState()
        state.load_from_directory(tmp_path)
        state.reset()
        assert not state.is_loaded

    def test_reset_cleans_temp_dir(self):
        temp = Path(tempfile.mkdtemp(prefix="test_spotify_"))
        (temp / "Playlist1.json.json").write_text(json.dumps(MINIMAL_PLAYLISTS))

        state = AppState()
        state.load_from_directory(temp)
        assert temp.exists()

        state.reset()
        assert not temp.exists()

    def test_load_replaces_previous_temp_dir(self):
        dir1 = Path(tempfile.mkdtemp(prefix="test_spotify_1_"))
        (dir1 / "Playlist1.json.json").write_text(json.dumps(MINIMAL_PLAYLISTS))

        dir2 = Path(tempfile.mkdtemp(prefix="test_spotify_2_"))
        (dir2 / "Playlist1.json.json").write_text(json.dumps(MINIMAL_PLAYLISTS))

        state = AppState()
        state.load_from_directory(dir1)
        state.load_from_directory(dir2)

        assert not dir1.exists()
        assert dir2.exists()

        state.reset()


# ---------------------------------------------------------------------------
# Middleware gating tests
# ---------------------------------------------------------------------------


class TestMiddlewareGating:
    def test_root_redirects_to_upload_when_no_data(self, client):
        resp = client.get("/")
        assert resp.status_code == 307
        assert resp.headers["location"] == "/upload"

    def test_playlists_redirects_when_no_data(self, client):
        resp = client.get("/playlists")
        assert resp.status_code == 307
        assert resp.headers["location"] == "/upload"

    def test_api_redirects_when_no_data(self, client):
        resp = client.get("/api/playlists/")
        assert resp.status_code == 307
        assert resp.headers["location"] == "/upload"

    def test_upload_page_accessible_without_data(self, client):
        resp = client.get("/upload")
        assert resp.status_code == 200

    def test_health_accessible_without_data(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data_loaded"] is False

    def test_static_accessible_without_data(self, client):
        resp = client.get("/static/css/custom.css")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Upload endpoint tests
# ---------------------------------------------------------------------------


class TestUpload:
    def test_valid_upload(self, client):
        zip_bytes = _valid_zip()
        resp = client.post(
            "/api/upload",
            files={"file": ("my_spotify_data.zip", zip_bytes, "application/zip")},
        )
        assert resp.status_code == 303
        assert resp.headers["location"] == "/"
        assert app_state.is_loaded

    def test_upload_non_zip(self, client):
        resp = client.post(
            "/api/upload",
            files={"file": ("bad.zip", b"not a zip file", "application/zip")},
        )
        assert resp.status_code == 400

    def test_upload_zip_missing_playlist_file(self, client):
        zip_bytes = _make_zip({"SomeOtherFile.json": {"foo": "bar"}})
        resp = client.post(
            "/api/upload",
            files={"file": ("data.zip", zip_bytes, "application/zip")},
        )
        assert resp.status_code == 400
        assert "Playlist1.json.json" in resp.json()["error"]

    def test_upload_replaces_previous_data(self, client):
        zip_bytes = _valid_zip()
        client.post(
            "/api/upload",
            files={"file": ("data.zip", zip_bytes, "application/zip")},
        )
        assert app_state.is_loaded

        # Upload again
        client.post(
            "/api/upload",
            files={"file": ("data2.zip", zip_bytes, "application/zip")},
        )
        assert app_state.is_loaded


# ---------------------------------------------------------------------------
# Reset endpoint tests
# ---------------------------------------------------------------------------


class TestReset:
    def test_reset_clears_data(self, client):
        # First upload
        zip_bytes = _valid_zip()
        client.post(
            "/api/upload",
            files={"file": ("data.zip", zip_bytes, "application/zip")},
        )
        assert app_state.is_loaded

        # Reset
        resp = client.post("/api/reset")
        assert resp.status_code == 303
        assert resp.headers["location"] == "/upload"
        assert not app_state.is_loaded

    def test_reset_when_no_data(self, client):
        resp = client.post("/api/reset")
        assert resp.status_code == 303


# ---------------------------------------------------------------------------
# End-to-end flow
# ---------------------------------------------------------------------------


class TestEndToEnd:
    def test_upload_then_browse_then_reset(self, client):
        # Initially redirected
        resp = client.get("/")
        assert resp.status_code == 307

        # Upload
        zip_bytes = _valid_zip()
        resp = client.post(
            "/api/upload",
            files={"file": ("data.zip", zip_bytes, "application/zip")},
        )
        assert resp.status_code == 303

        # Now pages work
        resp = client.get("/")
        assert resp.status_code == 200

        resp = client.get("/playlists")
        assert resp.status_code == 200

        # Health shows loaded
        resp = client.get("/health")
        assert resp.json()["data_loaded"] is True

        # Reset
        client.post("/api/reset")
        assert not app_state.is_loaded

        # Back to redirecting
        resp = client.get("/")
        assert resp.status_code == 307
