# deemon CLI Commands Reference

## Global Options

```
--init              Initialize or reset the appdata directory
--arl TOKEN         Set a new Deezer ARL token
-P, --profile NAME  Use a specific profile
-V, --version       Show version
-v, --verbose       Show debug output
-h, --help          Show help
```

Running `deemon` with no subcommand opens the **interactive menu** (full-screen TUI).

---

## `download` — Download music

```
deemon download [OPTIONS] [ARTIST]...
```

| Option | Description |
|--------|-------------|
| `-m, --monitored` | Download all currently monitored artists |
| `-i, --artist-id ID` | Download by Deezer artist ID(s) |
| `-A, --album-id ID` | Download by Deezer album ID(s) |
| `-T, --track-id ID` | Download by Deezer track ID(s) |
| `-u, --url URL` | Download from Deezer/Spotify/YouTube URL |
| `--artist-file PATH` | Download artists/IDs from file |
| `--album-file PATH` | Download album IDs or "Artist - Album" from file |
| `--track-file PATH` | Download track IDs from file |
| `-a, --after DATE` | Releases after this date (YYYY-MM-DD) |
| `-B, --before DATE` | Releases before this date |
| `-b, --bitrate N` | 128, 320, or FLAC |
| `-o, --download-path PATH` | Custom download directory |
| `-t, --record-type TYPE` | album, ep, single, or all |
| `-c, --collection-matcher` | Skip existing tracks (for playlists) |
| `--band NAME` | Band name (used with `--album`) |
| `--album NAME` | Album name (used with `--band`) |

**Args:** `ARTIST` can be "Artist Name" or "Artist - Album Name".

### Examples

```
deemon download "Radiohead - OK Computer"
deemon download --band "The Beatles" --album "Abbey Road"
deemon download -u "https://www.deezer.com/album/12345"
deemon download -m --bitrate FLAC
deemon download -i 123456 --record-type album
deemon download --album-file albums.txt
```

---

## `global` — Quick download by URL

```
deemon global URL
```

Alias for `deemon download -u URL`.

---

## `monitor` — Monitor artists for new releases

```
deemon monitor [OPTIONS] [ARTIST]...
```

| Option | Description |
|--------|-------------|
| `-a, --alerts` | Enable/disable email alerts |
| `-b, --bitrate N` | Specify download bitrate |
| `-D, --download` | Download all matching releases now |
| `-d, --download-path PATH` | Custom download directory |
| `-I, --import PATH` | Monitor artists/IDs from file or directory |
| `-i, --artist-id ID` | Monitor by Deezer artist ID |
| `-p, --playlist URL` | Monitor a Deezer playlist by URL |
| `--include-artists` | Also monitor artists found in playlist |
| `-u, --url URL` | Monitor artist by Deezer URL |
| `-R, --remove` | Stop monitoring an artist |
| `-s, --search` | Show similar results to choose from |
| `-T, --time-machine DATE` | Refresh as if it were this date |
| `-t, --record-type TYPE` | album, ep, single, or all |

### Examples

```
deemon monitor "Radiohead"
deemon monitor -u "https://www.deezer.com/artist/123"
deemon monitor -i 123456 --bitrate FLAC
deemon monitor -R "Some Artist"
deemon monitor -p "https://www.deezer.com/playlist/456" --include-artists
deemon monitor -I /path/to/artist-list.txt
```

---

## `refresh` — Check for new releases

```
deemon refresh [ARTIST]...
```

Checks all monitored artists (or specified ones) for new releases since last refresh. New releases are stored in the database and optionally downloaded.

| Option | Description |
|--------|-------------|
| `-T, --time-machine DATE` | Refresh as if it were this date |

---

## `playlist` — Download a playlist

```
deemon playlist [OPTIONS] URL
```

| Option | Description |
|--------|-------------|
| `-c, --collection-matcher` | Skip tracks already in local collection |
| `-b, --bitrate N` | Download bitrate |

---

## `discography` — Download complete discography

```
deemon discography [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-b, --band NAME` | Artist name |
| `-a, --album NAME` | Specific album |
| `-i, --artist-id ID` | Artist ID |
| `-u, --url URL` | Artist URL |
| `-B, --before DATE` | Only releases before this date |
| `-A, --after DATE` | Only releases after this date |
| `-t, --record-type TYPE` | album, ep, single, or all |
| `-o, --download-path PATH` | Custom download path |

---

## `show` — Display data

```
deemon show artists [OPTIONS]
deemon show playlists [OPTIONS]
deemon show releases [OPTIONS]
```

### show releases options

| Option | Description |
|--------|-------------|
| `-d, --days N` | Show releases from last N days (default: 7) |
| `-f, --future` | Show future releases |
| `--csv` | Output as CSV |

---

## `config` — Per-artist settings

```
deemon config "Artist Name"
```

Interactive per-artist configuration for bitrate, record type, alerts, download path.

---

## `search` — Interactive artist search

```
deemon search [QUERY]
```

Searches Deezer and presents an interactive picker. Selected artist can be downloaded or monitored.

---

## `profile` — Manage profiles

```
deemon profile
```

Manage multiple configuration profiles: create, switch, rename, delete.

---

## `backup` — Backup/restore

```
deemon backup [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-c, --create` | Create a backup archive |
| `-l, --list` | List available backups |
| `-r, --restore PATH` | Restore from backup |

---

## `rollback` — Undo refresh transactions

```
deemon rollback [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-v, --view` | View transaction history |
| `-n, --number N` | Rollback N most recent transactions |

---

## `test` — Verify configuration

```
deemon test [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-e, --email` | Test email notification |
| `-x, --exclusions` | Test exclusion patterns against releases |
| `-a, --arl` | Test ARL token validity |

---

## `extra` — Fetch release info

```
deemon extra
```

Fetches additional release metadata (record labels) for monitored artists. Hidden/developer command.

---

## `api` — Raw API access

```
deemon api
```

Interactive raw API viewer for testing. Hidden/developer command.

---

## `reset` — Reset monitoring data

```
deemon reset
```

Clears the monitoring database. Requires confirmation.

---

## `library upgrade` — Upgrade MP3 to FLAC (BETA)

```
deemon library upgrade
```

Scans download directories and upgrades MP3 files to FLAC when available. Experimental.
