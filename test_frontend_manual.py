"""Manual test for frontend pages.

This script tests that all HTML pages load correctly and contain expected content.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_index_page():
    """Test that index/dashboard page loads."""
    print("\n" + "=" * 70)
    print("TEST: Index Page (Dashboard)")
    print("=" * 70)
    response = client.get("/")
    print(f"Status: {response.status_code}")
    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "Spotify Data Tool" in response.text
    assert "Overview of your Spotify listening data" in response.text
    print("✅ PASSED - Index page loads with expected content")


def test_playlists_page():
    """Test that playlists page loads."""
    print("\n" + "=" * 70)
    print("TEST: Playlists Page")
    print("=" * 70)
    response = client.get("/playlists")
    print(f"Status: {response.status_code}")
    assert response.status_code == 200
    assert "Playlists" in response.text
    assert "Browse and explore all your playlists" in response.text
    assert "Search playlists" in response.text
    print("✅ PASSED - Playlists page loads with expected content")


def test_tracks_page():
    """Test that tracks page loads."""
    print("\n" + "=" * 70)
    print("TEST: Tracks Page")
    print("=" * 70)
    response = client.get("/tracks")
    print(f"Status: {response.status_code}")
    assert response.status_code == 200
    assert "Tracks" in response.text
    assert "Search and explore all your tracks" in response.text
    assert "Search tracks by name or artist" in response.text
    print("✅ PASSED - Tracks page loads with expected content")


def test_analytics_page():
    """Test that analytics page loads."""
    print("\n" + "=" * 70)
    print("TEST: Analytics Page")
    print("=" * 70)
    response = client.get("/analytics")
    print(f"Status: {response.status_code}")
    assert response.status_code == 200
    assert "Analytics Dashboard" in response.text
    assert "Explore your listening habits" in response.text
    assert "Most Common Tracks" in response.text
    assert "Most Played Tracks" in response.text
    print("✅ PASSED - Analytics page loads with expected content")


def test_all_pages_have_navigation():
    """Test that all pages have navigation."""
    print("\n" + "=" * 70)
    print("TEST: Navigation on All Pages")
    print("=" * 70)
    pages = ["/", "/playlists", "/tracks", "/analytics"]

    for page in pages:
        response = client.get(page)
        assert response.status_code == 200
        assert "Dashboard" in response.text
        assert "Playlists" in response.text
        assert "Tracks" in response.text
        assert "Analytics" in response.text
        print(f"✅ Navigation found on {page}")

    print("✅ PASSED - All pages have navigation")


def test_all_pages_have_footer():
    """Test that all pages have footer."""
    print("\n" + "=" * 70)
    print("TEST: Footer on All Pages")
    print("=" * 70)
    pages = ["/", "/playlists", "/tracks", "/analytics"]

    for page in pages:
        response = client.get(page)
        assert response.status_code == 200
        assert "Spotify Data Tool - Built with FastAPI" in response.text
        print(f"✅ Footer found on {page}")

    print("✅ PASSED - All pages have footer")


def test_all_pages_include_dependencies():
    """Test that all pages include required dependencies."""
    print("\n" + "=" * 70)
    print("TEST: Dependencies on All Pages")
    print("=" * 70)
    pages = ["/", "/playlists", "/tracks", "/analytics"]
    required_deps = [
        "tailwindcss.com",  # Tailwind CSS
        "htmx.org",  # HTMX
        "alpinejs",  # Alpine.js
    ]

    for page in pages:
        response = client.get(page)
        assert response.status_code == 200

        for dep in required_deps:
            assert dep in response.text, f"{dep} not found on {page}"

        print(f"✅ All dependencies found on {page}")

    print("✅ PASSED - All pages include required dependencies")


def test_analytics_page_has_charts():
    """Test that analytics page includes Chart.js charts."""
    print("\n" + "=" * 70)
    print("TEST: Charts on Analytics Page")
    print("=" * 70)
    response = client.get("/analytics")
    assert response.status_code == 200
    assert "chart.js" in response.text
    assert "playlist-chart" in response.text
    assert "plays-chart" in response.text
    assert "artists-chart" in response.text
    print("✅ PASSED - Analytics page includes all chart canvases")


def main():
    """Run all tests."""
    print("=" * 70)
    print("TESTING FRONTEND PAGES")
    print("=" * 70)

    tests = [
        test_index_page,
        test_playlists_page,
        test_tracks_page,
        test_analytics_page,
        test_all_pages_have_navigation,
        test_all_pages_have_footer,
        test_all_pages_include_dependencies,
        test_analytics_page_has_charts,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    print("=" * 70)

    if failed == 0:
        print("🎉 ALL FRONTEND TESTS PASSED!")
    else:
        print("⚠️  Some tests failed")

    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
