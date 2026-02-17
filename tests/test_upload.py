"""Tests for the file upload and extraction flow."""

import io
import json
import zipfile

import pytest
from starlette.testclient import TestClient

from main import app, app_state


@pytest.fixture(autouse=True)
def reset_app_state():
    """Ensure app state is clean before and after each test."""
    app_state.reset()
    yield
    app_state.reset()


def _make_zip(files: dict[str, bytes]) -> bytes:
    """Build an in-memory zip archive from a dict of {filename: content}."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


MINIMAL_PLAYLIST = json.dumps(
    {"playlists": [{"name": "Test", "lastModifiedDate": "2024-01-01", "items": []}]}
).encode()


@pytest.fixture
def valid_zip() -> bytes:
    """A minimal valid Spotify export zip."""
    return _make_zip({"Playlist1.json.json": MINIMAL_PLAYLIST})


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app, follow_redirects=False)


class TestUploadEndpoint:
    """Tests for POST /api/upload."""

    def test_upload_valid_zip(self, client, valid_zip):
        """Uploading a valid zip should load data and redirect to /."""
        resp = client.post(
            "/api/upload",
            files={"file": ("export.zip", valid_zip, "application/zip")},
        )

        assert resp.status_code == 303
        assert resp.headers["location"] == "/"
        assert app_state.is_loaded

    def test_upload_not_a_zip(self, client):
        """Uploading a non-zip file should return 400."""
        resp = client.post(
            "/api/upload",
            files={"file": ("bad.zip", b"not a zip file", "application/zip")},
        )

        assert resp.status_code == 400
        assert "not a valid zip" in resp.json()["error"]
        assert not app_state.is_loaded

    def test_upload_missing_playlist_file(self, client):
        """A zip without Playlist1.json.json should return 400."""
        zip_bytes = _make_zip({"SomeOtherFile.json": b"{}"})

        resp = client.post(
            "/api/upload",
            files={"file": ("export.zip", zip_bytes, "application/zip")},
        )

        assert resp.status_code == 400
        assert "Playlist1.json.json" in resp.json()["error"]
        assert not app_state.is_loaded

    def test_upload_path_traversal(self, client):
        """A zip with path traversal entries should be rejected."""
        zip_bytes = _make_zip(
            {
                "../evil.txt": b"gotcha",
                "Playlist1.json.json": MINIMAL_PLAYLIST,
            }
        )

        resp = client.post(
            "/api/upload",
            files={"file": ("export.zip", zip_bytes, "application/zip")},
        )

        assert resp.status_code == 400
        assert "unsafe path" in resp.json()["error"]
        assert not app_state.is_loaded

    def test_upload_replaces_previous_data(self, client, valid_zip):
        """Uploading a second time should replace the previous dataset."""
        client.post(
            "/api/upload",
            files={"file": ("first.zip", valid_zip, "application/zip")},
        )
        first_dir = app_state._temp_dir

        client.post(
            "/api/upload",
            files={"file": ("second.zip", valid_zip, "application/zip")},
        )

        assert app_state.is_loaded
        # The first temp dir should have been cleaned up
        assert not first_dir.exists()


class TestDataGating:
    """Tests that API routes require uploaded data."""

    def test_api_returns_403_without_upload(self, client):
        """API endpoints should return 403 when no data is loaded."""
        resp = client.get("/api/playlists/")

        assert resp.status_code == 403
        assert "No data loaded" in resp.json()["error"]
