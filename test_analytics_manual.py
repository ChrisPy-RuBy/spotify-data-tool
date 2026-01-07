"""Manual test for analytics module with real data.

This script tests analytics functions with actual Spotify data files.
"""

from pathlib import Path
from src.loaders import DataLoader
from src.analytics import (
    calculate_most_common_tracks_by_playlist,
    calculate_most_played_tracks,
    calculate_playlist_statistics,
    match_streaming_to_playlists,
    calculate_listening_time_stats,
    get_top_artists
)


def main():
    print("=" * 70)
    print("TESTING ANALYTICS ENGINE WITH REAL DATA")
    print("=" * 70)

    # Initialize data loader
    data_dir = Path("data")
    loader = DataLoader(data_dir)

    # Load data
    print("\n📂 Loading data...")
    playlists_data = loader.load_playlists_raw()
    streaming_history = loader.load_streaming_history_raw()

    print(f"✅ Loaded {len(playlists_data['playlists'])} playlists")
    print(f"✅ Loaded {len(streaming_history)} streaming events")

    # Test 1: Playlist Statistics
    print("\n" + "=" * 70)
    print("TEST 1: PLAYLIST STATISTICS")
    print("=" * 70)
    stats = calculate_playlist_statistics(playlists_data)

    print(f"Total Playlists: {stats['total_playlists']}")
    print(f"Total Items: {stats['total_items']}")
    print(f"Total Tracks: {stats['total_tracks']}")
    print(f"Total Episodes: {stats['total_episodes']}")
    print(f"Total Audiobooks: {stats['total_audiobooks']}")
    print(f"Total Local Tracks: {stats['total_local_tracks']}")
    print(f"Unique Tracks: {stats['unique_tracks']}")
    print(f"Avg Items per Playlist: {stats['avg_items_per_playlist']}")

    # Test 2: Most Common Tracks by Playlist
    print("\n" + "=" * 70)
    print("TEST 2: TOP 10 MOST COMMON TRACKS (by playlist appearance)")
    print("=" * 70)
    top_tracks_by_playlist = calculate_most_common_tracks_by_playlist(
        playlists_data,
        top_n=10
    )

    for i, track in enumerate(top_tracks_by_playlist, 1):
        print(f"{i:2d}. {track['track_name']} - {track['artist_name']}")
        print(f"    Appears in {track['playlist_count']} playlists")

    # Test 3: Most Played Tracks
    print("\n" + "=" * 70)
    print("TEST 3: TOP 10 MOST PLAYED TRACKS (from streaming history)")
    print("=" * 70)
    top_tracks_by_plays = calculate_most_played_tracks(
        streaming_history,
        top_n=10
    )

    for i, track in enumerate(top_tracks_by_plays, 1):
        print(f"{i:2d}. {track['track_name']} - {track['artist_name']}")
        print(f"    Played {track['play_count']} times")

    # Test 4: Listening Time Statistics
    print("\n" + "=" * 70)
    print("TEST 4: LISTENING TIME STATISTICS")
    print("=" * 70)
    time_stats = calculate_listening_time_stats(streaming_history)

    print(f"Total Listening Time:")
    print(f"  {time_stats['total_hours']:.1f} hours")
    print(f"  {time_stats['total_days']:.2f} days")
    print(f"Total Plays: {time_stats['total_plays']:,}")
    print(f"Average Play Duration: {time_stats['avg_minutes_per_play']:.1f} minutes")

    # Test 5: Top Artists
    print("\n" + "=" * 70)
    print("TEST 5: TOP 10 ARTISTS (by play count)")
    print("=" * 70)
    top_artists = get_top_artists(streaming_history, top_n=10)

    for i, artist in enumerate(top_artists, 1):
        hours = artist['total_minutes'] / 60
        print(f"{i:2d}. {artist['artist_name']}")
        print(f"    {artist['play_count']} plays | {hours:.1f} hours")

    # Test 6: Match Streaming to Playlists
    print("\n" + "=" * 70)
    print("TEST 6: STREAMING HISTORY MATCHED TO PLAYLISTS")
    print("=" * 70)
    matches = match_streaming_to_playlists(streaming_history, playlists_data)

    print(f"Total playlist tracks with streaming data: {len(matches)}")
    print(f"Total plays of playlist tracks: {sum(matches.values()):,}")

    # Show top 5 matched tracks
    print("\nTop 5 most played tracks that are in your playlists:")
    sorted_matches = sorted(matches.items(), key=lambda x: x[1], reverse=True)[:5]

    # Get track info from playlists
    track_info_map = {}
    for playlist in playlists_data['playlists']:
        for item in playlist['items']:
            if item.get('track'):
                uri = item['track'].get('trackUri')
                if uri and uri not in track_info_map:
                    track_info_map[uri] = {
                        'name': item['track'].get('trackName'),
                        'artist': item['track'].get('artistName')
                    }

    for i, (uri, play_count) in enumerate(sorted_matches, 1):
        if uri in track_info_map:
            info = track_info_map[uri]
            print(f"{i}. {info['name']} - {info['artist']}")
            print(f"   {play_count} plays")

    print("\n" + "=" * 70)
    print("✅ ALL ANALYTICS TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
