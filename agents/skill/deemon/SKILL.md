---
name: deemon
description: "Music monitoring and downloader CLI + MCP via Deezer. Use when the user wants to download music, search artists, monitor for new releases, refresh monitored artists, manage downloads, configure deemon, or interact with the Deezer music platform. Triggers on 'deemon', 'download music', 'monitor artist', 'deezer', 'album download', 'new releases', 'music download', 'deemon cheat sheet', 'deemon commands', 'deemon CLI'."
---

# deemon

deemon is both an MCP server and a CLI tool for monitoring and downloading music from Deezer. Agents with terminal access should prefer the CLI for downloads (it's faster and more flexible), and use the MCP for structured queries (search, list, info).

Set `DEEMON_ROOT` to the absolute path of this checkout before using the path examples below.

## CLI Quick Reference

```
deemon download "Artist - Album"        # download by name
deemon download --band "Artist" --album "Album"
deemon download --url "URL"             # download from URL
deemon global "URL"                     # download URL (alias)
deemon playlist "URL"                   # download playlist
deemon playlist -c "URL"               # skip existing tracks
deemon discography -b "Artist"          # download all albums

deemon monitor "Artist Name"            # monitor for new releases
deemon monitor -u "Artist URL"
deemon refresh                           # check all for new releases
deemon refresh "Artist Name"            # check specific artist
deemon show artists                      # list monitored artists
deemon show releases                     # recent releases (7 days)

deemon --arl YOUR_ARL_TOKEN              # set Deezer auth token
deemon config "Artist Name"              # per-artist settings
deemon profile                           # manage profiles
deemon -P "profile-name"                 # switch profile
deemon                                   # interactive menu
```

### Quality flags

```
-b, --bitrate N   1=128kbps, 3=320kbps, 9=FLAC
-o, --download-path PATH   custom location
-t, --record-type TYPE     album, ep, single, all
-v, --verbose              debug output
-h, --help                 help for any command
```

**Full CLI reference:** `references/commands.md` — every subcommand, flag, and example.

---

## MCP Server

The MCP server runs as a stdio process via the deemon venv. It is registered in opencode.json and available to all agents. It provides structured access to Deezer data without running CLI commands.

### Tools

| Tool | Params | Returns | When to use |
|------|--------|---------|-------------|
| `search_artists` | `query` (str), `limit` (int, default 10) | JSON list of `{id, name}` | Finding a Deezer artist ID to use with CLI commands |
| `get_artist_albums` | `artist_id` (int) | JSON list of releases with titles, dates, types | Browsing an artist's catalog before picking what to download |
| `get_album_info` | `album_id` (int) | JSON object with album metadata, track list, cover art | Checking album details before downloading |
| `download_album_by_name` | `artist_name` (str), `album_name` (str) | JSON status + download result | One-shot download without leaving the agent (prefer CLI for bulk) |
| `download_url` | `url` (str) | JSON status | Download from a Deezer/Spotify URL |
| `download_album` | `album_id` (int) | JSON status | Download by Deezer album ID |
| `download_track` | `track_id` (int) | JSON status | Download by Deezer track ID |
| `monitor_artist` | `artist_id` (int) | JSON status | Start monitoring from within the agent |
| `list_monitored_artists` | none | JSON list of monitored artists with metadata | Checking monitoring status |
| `list_recent_releases` | `days` (int, default 30) | JSON list of recent releases | What's new from monitored artists |

### When to use which

- **CLI** (`deemon download/monitor/refresh/config`) — for actual downloads, monitoring, and configuration. Faster, supports bulk ops, uses the full deemon feature set.
- **MCP** — for structured queries (search, list, album info) where you want parsed JSON back.

Both work with the same config and database.

---

## Database

File: `~/Library/Application Support/deemon/deemon.db` (macOS)

Key tables: `monitor` (artists), `releases` (albums), `playlists`, `playlist_tracks`, `profiles`, `transactions`, `deemon` (key-value metadata).

**Full schema:** `references/database.md` — all tables, columns, types, and useful SQL queries.

### Common tasks

```bash
# How many artists are being monitored?
bash scripts/deemon-query.sh 'SELECT COUNT(*) FROM monitor'

# What albums were found in the last 30 days?
bash scripts/deemon-query.sh \
  'SELECT artist_name, album_name, album_release FROM releases WHERE album_added > strftime("%s", "now", "-30 days")'

# Which artists haven't been refreshed yet?
bash scripts/deemon-query.sh 'SELECT artist_name, artist_id FROM monitor WHERE refreshed = 0'
```

---

## Configuration

File: `~/Library/Application Support/deemon/config.json` (macOS)

**Full schema:** `references/config.md` — every field with defaults, descriptions, and allowed values.

Key fields to check:
- `global.bitrate` — `128`, `320`, or `FLAC`
- `global.record_type` — `all`, `album`, `ep`, `single`
- `deemix.arl` — Deezer ARL token (required for downloads, 192 chars)
- `exclusions.patterns` / `exclusions.keywords` — filters applied during refresh

---

## Helper Scripts

Located in `scripts/` within the skill directory.

### `deemon-check.sh` — Health check

```bash
bash scripts/deemon-check.sh
```

Prints: Python venv status, CLI version, ARL token presence, current bitrate, config file location, database path/size/monitored count, deemix config status, download path. Run this first when troubleshooting.

### `deemon-query.sh` — SQL queries

```bash
bash scripts/deemon-query.sh 'SELECT artist_name, album_name FROM releases WHERE future_release=1'
```

Runs a read-only SQL query against deemon.db and prints a formatted table. Useful for quick checks without opening a SQLite shell.

---

## Paths

**Full reference:** `references/paths.md` — every important file path.

Key locations:

| What | Path |
|------|------|
| Project root | `$DEEMON_ROOT` |
| CLI entry | `<DEEMON_ROOT>/.venv/bin/deemon` |
| Config | `~/Library/Application Support/deemon/config.json` |
| Database | `~/Library/Application Support/deemon/deemon.db` |
| MCP server | `<DEEMON_ROOT>/scripts/deemon-mcp.py` |
| MCP agent config | `<DEEMON_ROOT>/agents/mcp/` |
| Skill root | `<DEEMON_ROOT>/agents/skill/deemon/` |

### Active venv

```bash
source "$DEEMON_ROOT/.venv/bin/activate"
deemon download "Artist - Album"
```

Or skip activation with the full path:
```bash
"$DEEMON_ROOT/.venv/bin/deemon" download "Artist - Album"
```
