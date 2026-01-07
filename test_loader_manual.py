"""
Quick manual test of the DataLoader to verify it works with real data.
This is a temporary test file - formal unit tests will go in tests/ directory.
"""

from pathlib import Path
from src.loaders import DataLoader

def test_loader():
    """Test that DataLoader can load all data files successfully."""

    print("🧪 Testing DataLoader with real Spotify data...\n")

    # Initialize loader
    data_dir = Path("data")
    loader = DataLoader(data_dir)

    # Test 1: Load playlists
    print("1️⃣ Testing playlist loading...")
    try:
        playlists_data = loader.load_playlists()
        print(f"   ✅ Loaded {len(playlists_data.playlists)} playlists")

        if playlists_data.playlists:
            first_playlist = playlists_data.playlists[0]
            print(f"   📁 First playlist: '{first_playlist.name}'")
            print(f"   🎵 Contains {len(first_playlist.items)} items")

            # Check first track
            for item in first_playlist.items:
                if item.track:
                    print(f"   🎶 First track: '{item.track.track_name}' by {item.track.artist_name}")
                    break

    except Exception as e:
        print(f"   ❌ Error loading playlists: {e}")
        return False

    print()

    # Test 2: Load streaming history
    print("2️⃣ Testing streaming history loading...")
    try:
        streaming_history = loader.load_streaming_history()
        print(f"   ✅ Loaded {len(streaming_history)} streaming events")

        if streaming_history:
            first_event = streaming_history[0]
            print(f"   🎧 First event: '{first_event.track_name}' by {first_event.artist_name}")
            print(f"   ⏱️  Played for {first_event.minutes_played:.2f} minutes")

    except Exception as e:
        print(f"   ❌ Error loading streaming history: {e}")
        return False

    print()

    # Test 3: Load library
    print("3️⃣ Testing library loading...")
    try:
        library_data = loader.load_library()
        print(f"   ✅ Loaded {len(library_data.tracks)} saved tracks")

        if library_data.tracks:
            first_track = library_data.tracks[0]
            print(f"   💾 First track: '{first_track.track}' by {first_track.artist}")

    except Exception as e:
        print(f"   ❌ Error loading library: {e}")
        return False

    print()

    # Test 4: Check caching
    print("4️⃣ Testing cache functionality...")
    cache_keys = loader.get_cache_keys()
    print(f"   ✅ Cache contains {len(cache_keys)} keys: {cache_keys}")

    print()
    print("🎉 All tests passed! DataLoader is working correctly.")
    return True


if __name__ == "__main__":
    success = test_loader()
    exit(0 if success else 1)
