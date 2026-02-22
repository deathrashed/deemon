# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**deemon** is a Python CLI tool that monitors artists for new releases, sends email notifications, and integrates with deemix to automatically download music from Deezer. It is a fork of the original [digitalec/deemon](https://github.com/digitalec/deemon) project.

## Development Commands

### Installation
```bash
# Quick install (editable mode, recommended for development)
./install.sh

# Install via pip in editable mode
pip install -e .

# Install from requirements
pip install -r requirements.txt
```

### Running
```bash
# Run directly via Python module
python3 -m deemon

# Run with specific command
python3 -m deemon --init
python3 -m deemon monitor "Artist Name"
python3 -m deemon refresh

# If installed globally
deemon COMMAND
```

### Key Commands for Development
```bash
deemon --init              # Initialize config/database
deemon monitor <artist>    # Monitor artist for new releases
deemon refresh             # Check all monitored artists for new releases
deemon download <artist>   # Download specific artist/album
deemon show artists        # List monitored artists
deemon show releases       # Show recent releases
deemon rollback -v         # View transaction history
deemon test -e             # Test email notification
deemon profile             # Manage configuration profiles
```

## Architecture

### Entry Points
- **`deemon/__main__.py`**: Main entry point, calls `cli.run()`
- **`deemon/cli.py`**: Click-based CLI framework with all command definitions and interactive menu

### Core Structure
```
deemon/
├── __main__.py           # Entry point
├── cli.py                # Click command definitions, interactive menu
├── core/
│   ├── api.py           # PlatformAPI - Deezer API wrapper (GW + public API)
│   ├── config.py        # Config class - JSON configuration management with validation
│   ├── db.py            # Database class - SQLite operations, transactions, migrations
│   ├── notifier.py      # Email notification handling
│   ├── logger.py        # Logging setup
│   ├── common.py        # Shared utilities (exclusion filters, etc.)
│   ├── exceptions.py    # Custom exceptions
│   └── dmi.py           # DeemixInterface - deemix library wrapper
├── cmd/
│   ├── monitor.py       # Monitor class - artist/playlist monitoring logic
│   ├── refresh.py       # Refresh class - check for new releases
│   ├── download.py      # Download class - queue and download music
│   ├── show.py          # Show class - display artists/playlists/releases
│   ├── search.py        # Search class - interactive artist search
│   ├── profile.py       # ProfileConfig - manage multiple profiles
│   ├── backup.py        # Backup/restore functionality
│   ├── rollback.py      # Transaction rollback
│   └── ...
└── utils/
    ├── startup.py       # Appdata directory initialization, paths
    ├── dataprocessor.py # CSV/file processing
    ├── validate.py      # Input validation
    ├── dates.py         # Date parsing utilities
    └── ui.py            # UI formatting constants
```

### Key Architectural Patterns

**PlatformAPI (`core/api.py`)**: Abstraction layer over Deezer's API. Can use either:
- GW API (faster, more threads via `fast_api_threads` config)
- Public API (slower, more reliable)

**Database (`core/db.py`)**: SQLite with:
- Transaction tracking for rollback support
- Profile-based data isolation
- Automatic migrations on startup

**Config (`core/config.py`)**: JSON-based configuration with:
- Automatic validation and migration of old settings
- Profile support for multiple configurations
- ARL token management for Deezer authentication

**Download Flow**:
1. `QueueItem` represents items to download
2. `Download.download()` builds queue from various sources
3. `Download.download_queue()` sends URLs to deemix via `DeemixInterface`
4. Optional Plex refresh after completion

### Data Flow

**Monitoring workflow**: `deemon monitor <artist>`
1. `Monitor.artists()` searches Deezer API for artist
2. User selects best match (interactive if needed)
3. Artist added to `monitor` table with config (bitrate, alerts, etc.)
4. `Refresh.run()` called automatically to fetch releases
5. New releases stored in `releases` table
6. Optional download and email notification

**Refresh workflow**: `deemon refresh`
1. Fetch all unrefreshed artists from database
2. Query Deezer API for artist discography
3. Apply filters (record type, exclusions, date range)
4. Store new releases in database
5. Queue downloads if enabled
6. Send email notifications if enabled

## Database Schema

- **monitor**: Monitored artists with per-artist config
- **releases**: Discovered releases (albums, EPs, singles)
- **playlists**: Monitored playlists
- **playlist_tracks**: Tracks from monitored playlists
- **transactions**: Transaction log for rollback support
- **profiles**: Multiple configuration profiles
- **deemon**: Metadata (version, update check, etc.)

## Important Configuration

- Config location: `~/.config/deemon/config.json` (macOS/Linux)
- Database location: `~/.local/share/deemon/deemon.db`
- ARL token: 192-character Deezer authentication token (required for downloads)
- Profile system: Allows separate configurations for different use cases

## Integration Points

- **Deemix**: Download engine (python-deemix package)
- **Deezer**: Music metadata source (deezer-python package)
- **Plex**: Optional library refresh after downloads (PlexAPI package)
- **Spotify**: Playlist monitoring via Spotify API (requires credentials)
- **Email**: SMTP notifications for new releases

## Development Notes

- Uses ThreadPoolExecutor for parallel API calls when monitoring multiple artists
- `fast_api` mode enables higher thread counts for GW API
- Transaction system allows undoing bulk operations via `deemon rollback`
- Exclusion filters use regex patterns and keyword matching
- Time machine mode (`-T DATE`) simulates refresh as if it were a past date
