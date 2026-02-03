# Data Analysis Notes

## Overview
This document provides analysis of the Spotify data dump files and how they relate to building the tool described in README.md.

## Tool Requirements (from README.md)
1. **Introspect all playlists** - View and analyze playlist data
2. **Introspect tracks** - View and analyze track information
3. **Overview Analytics section**:
   - Most common track in terms of playlist (appears in most playlists)
   - Most common track in terms of number of plays (from streaming history)

---

## Data Files Analysis

### Primary Files for Tool Implementation

#### 1. `Playlist1.json.json` (1.8MB, ~60k lines)
**Purpose**: Contains all user playlists with complete track listings

**Structure**:
```json
{
  "playlists": [
    {
      "name": "ESDS Social - 13.11.2025",
      "lastModifiedDate": "2025-11-13",
      "collaborators": [],
      "items": [
        {
          "track": {
            "trackName": "Blues in the News",
            "artistName": "Lionel Hampton",
            "albumName": "Flying Home",
            "trackUri": "spotify:track:6R6Sf9JTe06MrpCk7b3oW1"
          },
          "episode": null,
          "audiobook": null,
          "localTrack": null,
          "addedDate": "2025-11-11"
        }
      ]
    }
  ]
}
```

**Usage for Tool**:
- **Introspect all playlists**: Parse this file to display all playlists with names, dates, and track counts
- **Most common track by playlist**: Count how many playlists contain each unique track (by trackUri or trackName+artistName)
- Track metadata includes: trackName, artistName, albumName, trackUri, addedDate

**Key Insights**:
- Each playlist has a name, lastModifiedDate, and collaborators list
- Items can be tracks, episodes, audiobooks, or local tracks
- Use `trackUri` as unique identifier for tracks
- Total playlists can be counted from `playlists` array length

---

#### 2. `StreamingHistory_music_0.json.json` (328KB, ~12.6k lines)
**Purpose**: Complete music streaming/play history

**Structure**:
```json
[
  {
    "endTime": "2024-12-12 11:58",
    "artistName": "Unknown Artist",
    "trackName": "Unknown Track",
    "msPlayed": 55733
  },
  {
    "endTime": "2024-12-12 12:00",
    "artistName": "Dinah Washington",
    "trackName": "What A Great Sensation",
    "msPlayed": 157920
  }
]
```

**Usage for Tool**:
- **Most common track by plays**: Count occurrences of each track (by trackName+artistName combination)
- **Introspect tracks**: Show play counts, last played time, total listening time
- Can calculate:
  - Total plays per track
  - Total time listened per track (sum of msPlayed)
  - Most played artists
  - Listening patterns by date/time

**Key Insights**:
- ~12,600 streaming events recorded
- Each event has: endTime, artistName, trackName, msPlayed (milliseconds)
- Some tracks show as "Unknown Artist" / "Unknown Track"
- No unique track URI here, must match by trackName+artistName

---

#### 3. `YourLibrary.json.json` (501KB, ~15k lines)
**Purpose**: User's saved/liked tracks library

**Structure**:
```json
{
  "tracks": [
    {
      "artist": "Loyle Carner",
      "album": "Yesterday's Gone",
      "track": "Damselfly",
      "uri": "spotify:track:2QMihQt7YoEPkPNcDsAJf5"
    }
  ]
}
```

**Usage for Tool**:
- **Introspect tracks**: Display all saved tracks with artist, album info
- Can cross-reference with playlists and streaming history
- ~15,000 saved tracks in library
- Has `uri` field for unique track identification

**Key Insights**:
- This is the "Liked Songs" collection
- Contains: artist, album, track, uri
- Can be used to identify which library tracks appear in playlists
- Can be used to find library tracks that have never been played (cross-reference with streaming history)

---

### Secondary/Supporting Files

#### 4. `StreamingHistory_podcast_0.json.json` (41KB)
**Purpose**: Podcast streaming history
**Usage**: Could be used for future podcast analytics features

#### 5. `StreamingHistory_audiobook_0.json.json` (20KB)
**Purpose**: Audiobook streaming history
**Usage**: Could be used for future audiobook analytics features

#### 6. `Follow.json.json` (893B)
**Purpose**: Social following data

**Structure**:
```json
{
  "userIsFollowing": ["Song Exploder", "janeebonsall", ...],
  "userIsFollowedBy": ["12128436556", "morvenna21", ...],
  "userIsBlocking": []
}
```

**Usage**: Social features if needed (show followed users/artists)

#### 7. `SearchQueries.json.json` (36KB)
**Purpose**: Search history with timestamps and platforms

**Structure**:
```json
[
  {
    "platform": "IPHONE",
    "searchTime": "2025-09-15T19:56:58.327Z[UTC]",
    "searchQuery": "fela kuti",
    "searchInteractionURIs": ["spotify:artist:5CG9X521RDFWCuAhlo6QoR"]
  }
]
```

**Usage**: Could show search patterns, most searched artists/tracks

#### 8. `Inferences.json.json` (15KB)
**Purpose**: Spotify's algorithmic inferences about user preferences
**Usage**: Could display Spotify's categorization of user (genres, moods, etc.)

#### 9. `Marquee.json.json` (36KB)
**Purpose**: Promotional/marquee campaign data
**Usage**: Limited relevance for main tool features

#### 10. `MessageData.json.json` (686B)
**Purpose**: Message/communication data
**Usage**: Limited relevance for main tool features

---

## Implementation Strategy

### For "Introspect all playlists"
1. Parse `Playlist1.json.json`
2. Display each playlist with:
   - Name
   - Last modified date
   - Number of tracks
   - Optionally: list of all tracks in each playlist

### For "Introspect tracks"
1. Parse `YourLibrary.json.json` for all saved tracks
2. Optionally cross-reference with:
   - `StreamingHistory_music_0.json.json` to show play counts
   - `Playlist1.json.json` to show which playlists contain each track

### For "Most common track in terms of playlist"
1. Parse `Playlist1.json.json`
2. Count occurrences of each unique track across all playlists
3. Use `trackUri` as unique identifier (or fallback to trackName+artistName)
4. Sort by count descending
5. Display top N tracks

### For "Most common track in terms of number of plays"
1. Parse `StreamingHistory_music_0.json.json`
2. Count occurrences of each trackName+artistName combination
3. Sort by count descending
4. Display top N tracks with play counts
5. Optionally show total listening time (sum of msPlayed)

---

## Data Matching Considerations

**Challenge**: Different files use different identifiers
- `Playlist1.json.json` has `trackUri` (e.g., "spotify:track:...")
- `YourLibrary.json.json` has `uri`
- `StreamingHistory_music_0.json.json` only has trackName + artistName (no URI)

**Solution**:
- For playlist analysis: use `trackUri` as primary key
- For streaming history: use `trackName + artistName` as composite key
- For cross-referencing: may need fuzzy matching or accept that some matches won't be perfect
- Consider normalizing track names (lowercase, trim whitespace) for better matching

---

## Data Quality Notes

- Streaming history contains "Unknown Artist" / "Unknown Track" entries
- File naming has double `.json.json` extension
- Total dataset size: ~2.8MB
- Approximately 12,600 play events, 15,000 library tracks, and playlists containing thousands of tracks
