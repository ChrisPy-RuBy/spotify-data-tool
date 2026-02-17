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
    app_state.cleanup_all_sessions()
    yield
    app_state.cleanup_all_sessions()


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
        # Should set a session cookie
        assert "session_id" in resp.cookies

    def test_upload_not_a_zip(self, client):
        """Uploading a non-zip file should return 400."""
        resp = client.post(
            "/api/upload",
            files={"file": ("bad.zip", b"not a zip file", "application/zip")},
        )

        assert resp.status_code == 400
        assert "not a valid zip" in resp.json()["error"]
        # Should not set a session cookie
        assert "session_id" not in resp.cookies

    def test_upload_missing_playlist_file(self, client):
        """A zip without Playlist1.json.json should return 400."""
        zip_bytes = _make_zip({"SomeOtherFile.json": b"{}"})

        resp = client.post(
            "/api/upload",
            files={"file": ("export.zip", zip_bytes, "application/zip")},
        )

        assert resp.status_code == 400
        assert "Playlist1.json.json" in resp.json()["error"]
        assert "session_id" not in resp.cookies

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
        assert "session_id" not in resp.cookies

    def test_upload_nested_zip(self, client):
        """A zip with data files inside a subdirectory should work."""
        zip_bytes = _make_zip(
            {"my_spotify_data/Playlist1.json.json": MINIMAL_PLAYLIST}
        )

        resp = client.post(
            "/api/upload",
            files={"file": ("export.zip", zip_bytes, "application/zip")},
        )

        assert resp.status_code == 303
        assert "session_id" in resp.cookies
        # Get session from cookie and verify the loader is set up correctly
        session_cookie = resp.cookies["session_id"]
        from src.session import verify_session_id
        session_id = verify_session_id(session_cookie)
        loader = app_state.get_loader(session_id)
        assert loader is not None
        # DataLoader should point at the subdirectory, not the extraction root
        assert loader.data_directory.name == "my_spotify_data"

    def test_upload_replaces_previous_data(self, client, valid_zip):
        """Uploading a second time should create a new session."""
        resp1 = client.post(
            "/api/upload",
            files={"file": ("first.zip", valid_zip, "application/zip")},
        )
        session1_cookie = resp1.cookies["session_id"]
        from src.session import verify_session_id, session_manager
        session1_id = verify_session_id(session1_cookie)
        session1_data = session_manager.get_session_data(session1_id)
        first_dir = session1_data["extract_root"]

        resp2 = client.post(
            "/api/upload",
            files={"file": ("second.zip", valid_zip, "application/zip")},
        )
        session2_cookie = resp2.cookies["session_id"]
        session2_id = verify_session_id(session2_cookie)

        # Should create a different session
        assert session1_id != session2_id
        # Both sessions should exist
        assert app_state.get_loader(session1_id) is not None
        assert app_state.get_loader(session2_id) is not None
        # The first temp dir should still exist (not cleaned up automatically)
        assert first_dir.exists()


class TestDataGating:
    """Tests that routes require uploaded data."""

    def test_api_returns_403_without_upload(self, client):
        """API endpoints should return 403 when no data is loaded."""
        resp = client.get("/api/playlists/")

        assert resp.status_code == 403
        assert "No data loaded" in resp.json()["error"]

    def test_pages_redirect_to_upload_without_data(self, client):
        """Page routes should redirect to /upload when no data is loaded."""
        for path in ("/", "/playlists", "/tracks", "/analytics"):
            resp = client.get(path)
            assert resp.status_code == 307, f"{path} should redirect"
            assert resp.headers["location"] == "/upload"

    def test_upload_page_accessible_without_data(self, client):
        """The upload page itself should always be accessible."""
        resp = client.get("/upload")
        assert resp.status_code == 200
        assert "Upload Your Spotify Data" in resp.text

    def test_health_accessible_without_data(self, client):
        """The health endpoint should not be gated."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_no_redirect_after_upload(self, client, valid_zip):
        """Pages should render normally after data is uploaded."""
        resp1 = client.post(
            "/api/upload",
            files={"file": ("export.zip", valid_zip, "application/zip")},
        )
        # Get the session cookie from the upload response
        session_cookie = resp1.cookies.get("session_id")

        # Make request with the session cookie
        resp = client.get("/", cookies={"session_id": session_cookie})
        assert resp.status_code == 200
        assert "Dashboard" in resp.text


class TestResetEndpoint:
    """Tests for POST /api/reset."""

    def test_reset_clears_data_and_redirects(self, client, valid_zip):
        """Resetting should clear session and redirect to /upload."""
        resp1 = client.post(
            "/api/upload",
            files={"file": ("export.zip", valid_zip, "application/zip")},
        )
        session_cookie = resp1.cookies["session_id"]
        from src.session import verify_session_id
        session_id = verify_session_id(session_cookie)
        assert app_state.get_loader(session_id) is not None

        # Make request with session cookie set
        resp = client.post("/api/reset", cookies={"session_id": session_cookie})

        assert resp.status_code == 303
        assert resp.headers["location"] == "/upload"
        # Session should be deleted
        assert app_state.get_loader(session_id) is None

    def test_reset_cleans_up_temp_dir(self, client, valid_zip):
        """Resetting should remove the temporary extraction directory."""
        resp1 = client.post(
            "/api/upload",
            files={"file": ("export.zip", valid_zip, "application/zip")},
        )
        session_cookie = resp1.cookies["session_id"]
        from src.session import verify_session_id, session_manager
        session_id = verify_session_id(session_cookie)
        session_data = session_manager.get_session_data(session_id)
        temp_dir = session_data["extract_root"]
        assert temp_dir.exists()

        client.post("/api/reset", cookies={"session_id": session_cookie})

        assert not temp_dir.exists()

    def test_reset_when_no_data_loaded(self, client):
        """Resetting with no data loaded should still redirect cleanly."""
        resp = client.post("/api/reset")

        assert resp.status_code == 303
        assert resp.headers["location"] == "/upload"

    def test_nav_shows_reset_button_when_data_loaded(self, client, valid_zip):
        """The nav bar should show a reset button when data is loaded."""
        resp1 = client.post(
            "/api/upload",
            files={"file": ("export.zip", valid_zip, "application/zip")},
        )
        session_cookie = resp1.cookies.get("session_id")

        resp = client.get("/", cookies={"session_id": session_cookie})
        assert "Reset Data" in resp.text

    def test_upload_page_hides_reset_button(self, client):
        """The upload page should not show the reset button."""
        resp = client.get("/upload")
        assert "Reset Data" not in resp.text


class TestLifespanCleanup:
    """Tests that server shutdown cleans up temporary data."""

    def test_shutdown_cleans_up_temp_dir(self, valid_zip):
        """Manual cleanup should remove temporary directories."""
        temp_dir = None
        from src.session import session_manager
        
        # Test with a regular TestClient
        client = TestClient(app)
        resp = client.post(
            "/api/upload",
            files={"file": ("export.zip", valid_zip, "application/zip")},
            follow_redirects=False
        )
        
        # Get session cookie - it's in the set-cookie header
        assert resp.status_code == 303
        assert "session_id" in resp.cookies
        
        session_cookie = resp.cookies.get("session_id")
        assert session_cookie is not None
        
        from src.session import verify_session_id
        session_id = verify_session_id(session_cookie)
        session_data = session_manager.get_session_data(session_id)
        temp_dir = session_data["extract_root"]
        assert temp_dir.exists()
        
        # Manually trigger cleanup
        app_state.cleanup_all_sessions()

        # After cleanup, temp directory should be gone
        assert not temp_dir.exists()
