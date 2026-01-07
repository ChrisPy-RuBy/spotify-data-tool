"""Manual test for FastAPI endpoints with real data.

This script tests all API endpoints with actual Spotify data.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    print("\n" + "=" * 70)
    print("TEST: Health Check")
    print("=" * 70)
    response = client.get("/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✅ PASSED")


def test_analytics_overview():
    """Test analytics overview endpoint."""
    print("\n" + "=" * 70)
    print("TEST: Analytics Overview")
    print("=" * 70)
    response = client.get("/api/analytics/overview")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total Playlists: {data['playlists']['total']}")
    print(f"Total Tracks: {data['playlists']['total_tracks']}")
    print(f"Total Plays: {data['streaming']['total_plays']}")
    print(f"Total Hours: {data['streaming']['total_hours']}")
    assert response.status_code == 200
    assert data['playlists']['total'] > 0
    print("✅ PASSED")


def test_top_tracks_by_playlist():
    """Test top tracks by playlist endpoint."""
    print("\n" + "=" * 70)
    print("TEST: Top Tracks by Playlist")
    print("=" * 70)
    response = client.get("/api/analytics/top-tracks-by-playlist?limit=5")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Returned {len(data)} tracks")
    if data:
        print("\nTop 5:")
        for i, track in enumerate(data, 1):
            print(f"{i}. {track['track_name']} - {track['artist_name']}")
            print(f"   Appears in {track['playlist_count']} playlists")
    assert response.status_code == 200
    assert len(data) > 0
    print("✅ PASSED")


def test_top_tracks_by_plays():
    """Test top tracks by plays endpoint."""
    print("\n" + "=" * 70)
    print("TEST: Top Tracks by Plays")
    print("=" * 70)
    response = client.get("/api/analytics/top-tracks-by-plays?limit=5")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Returned {len(data)} tracks")
    if data:
        print("\nTop 5:")
        for i, track in enumerate(data, 1):
            print(f"{i}. {track['track_name']} - {track['artist_name']}")
            print(f"   {track['play_count']} plays")
    assert response.status_code == 200
    print("✅ PASSED")


def test_top_artists():
    """Test top artists endpoint."""
    print("\n" + "=" * 70)
    print("TEST: Top Artists")
    print("=" * 70)
    response = client.get("/api/analytics/top-artists?limit=5")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Returned {len(data)} artists")
    if data:
        print("\nTop 5:")
        for i, artist in enumerate(data, 1):
            print(f"{i}. {artist['artist_name']}")
            print(f"   {artist['play_count']} plays, {artist['total_minutes']} minutes")
    assert response.status_code == 200
    print("✅ PASSED")


def test_list_playlists():
    """Test list playlists endpoint."""
    print("\n" + "=" * 70)
    print("TEST: List Playlists")
    print("=" * 70)
    response = client.get("/api/playlists/?limit=5")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total playlists: {data['total']}")
    print(f"Returned: {data['count']}")
    if data['playlists']:
        print("\nFirst 5:")
        for playlist in data['playlists']:
            print(f"- {playlist['name']}: {playlist['total_items']} items")
    assert response.status_code == 200
    assert data['total'] > 0
    print("✅ PASSED")


def test_get_specific_playlist():
    """Test get specific playlist endpoint."""
    print("\n" + "=" * 70)
    print("TEST: Get Specific Playlist")
    print("=" * 70)

    # First get a playlist name
    list_response = client.get("/api/playlists/?limit=1")
    playlist_name = list_response.json()['playlists'][0]['name']

    # Now get the full playlist
    response = client.get(f"/api/playlists/{playlist_name}")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Playlist: {data['name']}")
    print(f"Total items: {data['total_items']}")
    print(f"Tracks: {data.get('track_count', 0)}")
    assert response.status_code == 200
    print("✅ PASSED")


def test_search_playlists():
    """Test search playlists endpoint."""
    print("\n" + "=" * 70)
    print("TEST: Search Playlists")
    print("=" * 70)
    response = client.get("/api/playlists/search/by-name?query=20")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data)} playlists matching '20'")
    for playlist in data[:3]:
        print(f"- {playlist['name']}")
    assert response.status_code == 200
    print("✅ PASSED")


def test_list_tracks():
    """Test list tracks endpoint."""
    print("\n" + "=" * 70)
    print("TEST: List Tracks")
    print("=" * 70)
    response = client.get("/api/tracks/?limit=5")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total unique tracks: {data['total']}")
    print(f"Returned: {data['count']}")
    if data['tracks']:
        print("\nFirst 5:")
        for track in data['tracks'][:5]:
            print(f"- {track['track_name']} - {track['artist_name']}")
    assert response.status_code == 200
    assert data['total'] > 0
    print("✅ PASSED")


def test_search_tracks():
    """Test search tracks endpoint."""
    print("\n" + "=" * 70)
    print("TEST: Search Tracks")
    print("=" * 70)
    response = client.get("/api/tracks/search?query=love&limit=5")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data)} tracks matching 'love'")
    for track in data:
        print(f"- {track['track_name']} - {track['artist_name']}")
    assert response.status_code == 200
    print("✅ PASSED")


def test_matched_tracks():
    """Test matched tracks endpoint."""
    print("\n" + "=" * 70)
    print("TEST: Matched Tracks (Streaming to Playlists)")
    print("=" * 70)
    response = client.get("/api/analytics/matched-tracks?limit=5")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total matched tracks: {data['total_matched_tracks']}")
    print(f"Total plays: {data['total_plays']}")
    if data['tracks']:
        print("\nTop 5 matched tracks:")
        for track in data['tracks']:
            print(f"- {track['track_name']} - {track['artist_name']}")
            print(f"  {track['play_count']} plays")
    assert response.status_code == 200
    print("✅ PASSED")


def main():
    """Run all tests."""
    print("=" * 70)
    print("TESTING FASTAPI ENDPOINTS WITH REAL DATA")
    print("=" * 70)

    tests = [
        test_health_check,
        test_analytics_overview,
        test_top_tracks_by_playlist,
        test_top_tracks_by_plays,
        test_top_artists,
        test_list_playlists,
        test_get_specific_playlist,
        test_search_playlists,
        test_list_tracks,
        test_search_tracks,
        test_matched_tracks,
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
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  Some tests failed")

    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
