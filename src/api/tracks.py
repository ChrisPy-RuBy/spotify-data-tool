"""Tracks API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from src.loaders import DataLoader

router = APIRouter()


def get_data_loader() -> DataLoader:
    """Dependency to get data loader from main app."""
    from main import data_loader
    return data_loader


@router.get("/")
async def list_tracks(
    limit: Optional[int] = 100,
    offset: int = 0,
    loader: DataLoader = Depends(get_data_loader),
) -> dict:
    """List all unique tracks from playlists.

    Args:
        limit: Maximum number of tracks to return (default: 100)
        offset: Number of tracks to skip (default: 0)

    Returns:
        Dictionary with tracks and metadata
    """
    playlists_data = loader.load_playlists_raw()

    # Build unique tracks map using URI as key
    unique_tracks = {}
    for playlist in playlists_data.get("playlists", []):
        for item in playlist.get("items", []):
            track = item.get("track")
            if track:
                uri = track.get("trackUri")
                if uri and uri not in unique_tracks:
                    unique_tracks[uri] = {
                        "track_uri": uri,
                        "track_name": track.get("trackName", "Unknown"),
                        "artist_name": track.get("artistName", "Unknown"),
                        "album_name": track.get("albumName", "Unknown"),
                    }

    # Convert to list and apply pagination
    all_tracks = list(unique_tracks.values())
    total = len(all_tracks)

    tracks_slice = all_tracks[offset:]
    if limit:
        tracks_slice = tracks_slice[:limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "count": len(tracks_slice),
        "tracks": tracks_slice,
    }


@router.get("/search")
async def search_tracks(
    query: str,
    limit: int = 50,
    offset: int = 0,
    album: Optional[str] = None,
    loader: DataLoader = Depends(get_data_loader),
) -> dict:
    """Search tracks by name or artist with pagination and optional album filter.

    Args:
        query: Search query string
        limit: Maximum number of results (default: 50)
        offset: Number of tracks to skip (default: 0)
        album: Optional album name filter

    Returns:
        Dictionary with matching tracks and metadata
    """
    playlists_data = loader.load_playlists_raw()

    query_lower = query.lower()
    album_lower = album.lower() if album else None
    matching_tracks = {}

    for playlist in playlists_data.get("playlists", []):
        for item in playlist.get("items", []):
            track = item.get("track")
            if track:
                uri = track.get("trackUri")
                track_name = track.get("trackName", "")
                artist_name = track.get("artistName", "")
                album_name = track.get("albumName", "Unknown")

                # Check if query matches track name or artist name
                if (
                    query_lower in track_name.lower()
                    or query_lower in artist_name.lower()
                ):
                    # Apply album filter if specified
                    if album_lower and album_lower not in album_name.lower():
                        continue

                    if uri and uri not in matching_tracks:
                        matching_tracks[uri] = {
                            "track_uri": uri,
                            "track_name": track_name,
                            "artist_name": artist_name,
                            "album_name": album_name,
                        }

    # Apply pagination
    all_tracks = list(matching_tracks.values())
    total = len(all_tracks)
    tracks_slice = all_tracks[offset:]
    if limit:
        tracks_slice = tracks_slice[:limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "count": len(tracks_slice),
        "query": query,
        "album_filter": album,
        "tracks": tracks_slice,
    }


@router.get("/albums")
async def list_albums(
    limit: int = 100,
    offset: int = 0,
    query: Optional[str] = None,
    loader: DataLoader = Depends(get_data_loader),
) -> dict:
    """List unique albums with track counts.

    Args:
        limit: Maximum number of albums to return (default: 100)
        offset: Number of albums to skip (default: 0)
        query: Optional search query for album names

    Returns:
        Dictionary with albums and metadata
    """
    playlists_data = loader.load_playlists_raw()

    # Build album map with track counts
    albums = {}
    query_lower = query.lower() if query else None

    for playlist in playlists_data.get("playlists", []):
        for item in playlist.get("items", []):
            track = item.get("track")
            if track:
                album_name = track.get("albumName", "Unknown")
                artist_name = track.get("artistName", "Unknown")
                album_key = f"{album_name}||{artist_name}"

                # Apply search filter if query provided
                if query_lower and query_lower not in album_name.lower():
                    continue

                if album_key not in albums:
                    albums[album_key] = {
                        "album_name": album_name,
                        "artist_name": artist_name,
                        "track_count": 0,
                    }
                albums[album_key]["track_count"] += 1

    # Sort by track count descending
    all_albums = sorted(albums.values(), key=lambda x: x["track_count"], reverse=True)
    total = len(all_albums)

    # Apply pagination
    albums_slice = all_albums[offset:]
    if limit:
        albums_slice = albums_slice[:limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "count": len(albums_slice),
        "query": query,
        "albums": albums_slice,
    }


@router.get("/filter")
async def filter_tracks(
    album: Optional[str] = None,
    artist: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    loader: DataLoader = Depends(get_data_loader),
) -> dict:
    """Filter tracks by album and/or artist.

    Args:
        album: Optional album name filter
        artist: Optional artist name filter
        limit: Maximum number of tracks to return (default: 50)
        offset: Number of tracks to skip (default: 0)

    Returns:
        Dictionary with filtered tracks and metadata
    """
    playlists_data = loader.load_playlists_raw()

    album_lower = album.lower() if album else None
    artist_lower = artist.lower() if artist else None
    matching_tracks = {}

    for playlist in playlists_data.get("playlists", []):
        for item in playlist.get("items", []):
            track = item.get("track")
            if track:
                uri = track.get("trackUri")
                track_name = track.get("trackName", "")
                artist_name = track.get("artistName", "")
                album_name = track.get("albumName", "Unknown")

                # Apply filters
                if album_lower and album_lower not in album_name.lower():
                    continue
                if artist_lower and artist_lower not in artist_name.lower():
                    continue

                if uri and uri not in matching_tracks:
                    matching_tracks[uri] = {
                        "track_uri": uri,
                        "track_name": track_name,
                        "artist_name": artist_name,
                        "album_name": album_name,
                    }

    # Apply pagination
    all_tracks = list(matching_tracks.values())
    total = len(all_tracks)
    tracks_slice = all_tracks[offset:]
    if limit:
        tracks_slice = tracks_slice[:limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "count": len(tracks_slice),
        "album_filter": album,
        "artist_filter": artist,
        "tracks": tracks_slice,
    }


@router.get("/{track_uri:path}")
async def get_track_details(
    track_uri: str, loader: DataLoader = Depends(get_data_loader)
) -> dict:
    """Get details for a specific track by URI.

    Args:
        track_uri: Spotify track URI (e.g., spotify:track:123)

    Returns:
        Track details including which playlists contain it

    Raises:
        HTTPException: If track not found
    """
    playlists_data = loader.load_playlists_raw()

    track_info = None
    found_in_playlists = []

    for playlist in playlists_data.get("playlists", []):
        for item in playlist.get("items", []):
            track = item.get("track")
            if track and track.get("trackUri") == track_uri:
                # Store track info (only once)
                if not track_info:
                    track_info = {
                        "track_uri": track_uri,
                        "track_name": track.get("trackName", "Unknown"),
                        "artist_name": track.get("artistName", "Unknown"),
                        "album_name": track.get("albumName", "Unknown"),
                    }

                # Track which playlists contain this track
                found_in_playlists.append(
                    {
                        "playlist_name": playlist.get("name", "Untitled"),
                        "added_date": item.get("addedDate", "Unknown"),
                    }
                )

    if not track_info:
        raise HTTPException(status_code=404, detail=f"Track '{track_uri}' not found")

    track_info["found_in_playlists"] = found_in_playlists
    track_info["playlist_count"] = len(found_in_playlists)

    return track_info


@router.get("/by-artist/{artist_name}")
async def get_tracks_by_artist(
    artist_name: str,
    limit: int = 100,
    loader: DataLoader = Depends(get_data_loader),
) -> List[dict]:
    """Get all tracks by a specific artist.

    Args:
        artist_name: Artist name to search for
        limit: Maximum number of tracks to return (default: 100)

    Returns:
        List of tracks by the artist
    """
    playlists_data = loader.load_playlists_raw()

    artist_lower = artist_name.lower()
    artist_tracks = {}

    for playlist in playlists_data.get("playlists", []):
        for item in playlist.get("items", []):
            track = item.get("track")
            if track:
                track_artist = track.get("artistName", "")
                if artist_lower in track_artist.lower():
                    uri = track.get("trackUri")
                    if uri and uri not in artist_tracks:
                        artist_tracks[uri] = {
                            "track_uri": uri,
                            "track_name": track.get("trackName", "Unknown"),
                            "artist_name": track_artist,
                            "album_name": track.get("albumName", "Unknown"),
                        }

                if len(artist_tracks) >= limit:
                    break

        if len(artist_tracks) >= limit:
            break

    return list(artist_tracks.values())[:limit]
