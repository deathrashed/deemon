# deemon Database Reference

Database file: `~/Library/Application Support/deemon/deemon.db` (macOS) or `~/.config/deemon/deemon.db` (Linux)

Schema version: `3.7`

## Tables

### `monitor` — Monitored artists

```sql
CREATE TABLE monitor (
    artist_id     INTEGER,
    artist_name   TEXT,
    bitrate       TEXT,
    record_type   TEXT,
    alerts        INTEGER,
    profile_id    INTEGER DEFAULT 1,
    download_path TEXT,
    refreshed     INTEGER DEFAULT 0,
    trans_id      INTEGER
);
```

| Column | Notes |
|--------|-------|
| `artist_id` | Deezer artist ID |
| `refreshed` | 0 = needs refresh, 1 = already refreshed |
| `trans_id` | Links to transactions table for rollback |
| `profile_id` | Separates monitoring per profile |

### `releases` — Albums seen for monitored artists

```sql
CREATE TABLE releases (
    artist_id      INTEGER,
    artist_name    TEXT,
    album_id       INTEGER,
    album_name     TEXT,
    album_release  TEXT,
    album_added    INTEGER,
    explicit       INTEGER,
    label          TEXT,
    record_type    INTEGER,
    profile_id     INTEGER DEFAULT 1,
    future_release INTEGER DEFAULT 0,
    trans_id       INTEGER,
    UNIQUE(album_id, profile_id)
);
```

| Column | Notes |
|--------|-------|
| `album_release` | Date string "YYYY-MM-DD" |
| `album_added` | Unix timestamp when first seen |
| `record_type` | 0=single, 1=album, 2=compilation, 3=ep |
| `future_release` | 1 if release date is in future |

### `playlists` — Monitored playlists

```sql
CREATE TABLE playlists (
    id              INTEGER UNIQUE,
    title           TEXT,
    url             TEXT,
    bitrate         TEXT,
    alerts          INTEGER,
    profile_id      INTEGER DEFAULT 1,
    download_path   TEXT,
    refreshed       INTEGER DEFAULT 0,
    trans_id        INTEGER,
    monitor_artists INTEGER DEFAULT 0
);
```

### `playlist_tracks` — Tracks seen in playlists

```sql
CREATE TABLE playlist_tracks (
    track_id     INTEGER,
    playlist_id  INTEGER,
    artist_id    INTEGER,
    artist_name  TEXT,
    track_name   TEXT,
    profile_id   INTEGER DEFAULT 1,
    track_added  TEXT,
    trans_id     INTEGER
);
```

### `deemon` — Key-value metadata store

```sql
CREATE TABLE deemon (
    property TEXT,
    value    TEXT
);
```

Stored properties: `version`, `latest_ver`, `last_update_check`, `release_channel`.

### `profiles` — Configuration profiles

```sql
CREATE TABLE profiles (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT,
    email         TEXT,
    alerts        INTEGER,
    bitrate       TEXT,
    record_type   TEXT,
    plex_baseurl  TEXT,
    plex_token    TEXT,
    plex_library  TEXT,
    download_path TEXT
);
```

### `transactions` — Refresh operations (for rollback)

```sql
CREATE TABLE transactions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp  INTEGER,
    profile_id INTEGER DEFAULT 1
);
```

## Useful Queries

### What's new in the last N days
```sql
SELECT r.artist_name, r.album_name, r.album_release, r.record_type
FROM releases r
WHERE r.album_added > strftime('%s', 'now', '-30 days')
  AND r.profile_id = 1
ORDER BY r.album_added DESC;
```

### Artists due for refresh
```sql
SELECT artist_name, artist_id FROM monitor
WHERE refreshed = 0 AND profile_id = 1;
```

### Full artist monitoring status
```sql
SELECT m.artist_name, m.bitrate, m.record_type,
       CASE WHEN m.refreshed THEN 'done' ELSE 'pending' END AS status,
       COUNT(r.album_id) AS total_releases
FROM monitor m
LEFT JOIN releases r ON r.artist_id = m.artist_id AND r.profile_id = m.profile_id
WHERE m.profile_id = 1
GROUP BY m.artist_id
ORDER BY m.artist_name;
```

### Future releases
```sql
SELECT artist_name, album_name, album_release
FROM releases
WHERE future_release = 1 AND profile_id = 1
ORDER BY album_release;
```

## Record Type Mapping

| Value | Type |
|-------|------|
| 0 | single |
| 1 | album |
| 2 | compilation |
| 3 | ep |

## Migration History

| From | To | Change |
|------|----|--------|
| < 3.5 | | Error: must upgrade to v2.5 first |
| < 3.5.2 | 3.5.2 | Added `future_release` column to releases |
| < 3.6 | 3.6 | Removed `album_release_ts` column |
| < 3.7 | 3.7 | Added `monitor_artists` column to playlists |
