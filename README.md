<img src="deemon/assets/images/deemon.png" alt="deemon" width="300">

[About](#about) | [Installation](#installation) | [Docker](#docker) | [Configuration](#configuration) | [Commands](#commands) | [Examples](#examples) | [Support](#support)

![PyPI](https://img.shields.io/pypi/v/deemon?style=for-the-badge)
![Downloads](https://img.shields.io/pepy/dt/deemon?style=for-the-badge)
![GitHub last release](https://img.shields.io/github/release-date/digitalec/deemon?style=for-the-badge)
![GitHub last commit](https://img.shields.io/github/last-commit/digitalec/deemon?style=for-the-badge)
![Docker](https://img.shields.io/github/actions/workflow/status/digitalec/deemon/deploy-docker.yml?branch=main&style=for-the-badge&logo=docker)
![Discord](https://img.shields.io/discord/831356172464160838?style=for-the-badge&logo=discord)

## About

deemon is a command line tool written in Python that monitors artists for new releases, provides email notifications, and integrates with the deemix library to automatically download new releases from Deezer.

### Features

- **Artist Monitoring**: Track multiple artists and receive alerts when new releases are available
- **Automatic Downloads**: Automatically download new releases using deemix integration
- **Playlist Support**: Monitor and download from Spotify and Deezer playlists
- **Email Notifications**: Get notified via email when new releases are detected
- **Flexible Configuration**: Per-artist settings, multiple profiles, and extensive customization
- **Batch Operations**: Download from files, monitor multiple artists at once
- **Release Filtering**: Filter by record type (album, EP, single), exclude patterns/keywords
- **Plex Integration**: Optional integration with Plex Media Server
- **Spotify Integration**: Import and monitor from Spotify playlists
- **Transaction Management**: Rollback monitoring changes if needed
- **Interactive Menu**: User-friendly TUI with styled menus and pagination
- **Keyboard Maestro Ready**: Wrapper script included for automation workflows

## Support

[Open an Issue](https://github.com/digitalec/deemon/issues/new) | [Discord](https://discord.gg/KzNCG2tkvn)

## Installation

### Prerequisites

- Python 3.8 or higher
- Deezer account with ARL (Authentication Reference Length) token for downloads
- deemix library (automatically installed as dependency)

### Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/digitalec/deemon.git ~/deemon
cd ~/deemon

# Run the install script
./install.sh
```

The install script will:
- Install deemon in **editable mode** (changes take effect immediately)
- Set up the `deemon` command globally
- Configure proper paths for Keyboard Maestro/automation tools

### Using pip

```bash
$ pip install deemon
```

### From source

```bash
$ git clone https://github.com/digitalec/deemon.git ~/deemon
$ cd ~/deemon
$ pip install -r requirements.txt
$ python3 -m deemon
```

### Docker

Docker support is available for `amd64`, `arm64`, and `armv7` architectures. It is recommended to save your `docker run` command as a script to execute via cron/Task Scheduler.

**Note:** Inside deemon's `config.json`, download_location **must** be set to `/downloads`.

**Example: Refreshing an existing database**
```bash
docker run --name deemon \
       --rm \
       -v /path/to/deemon/config:/config \
       -v /path/to/music:/downloads \
       -v /path/to/deemix/config:/deemix  \
       ghcr.io/digitalec/deemon:latest \
       python3 -m deemon refresh
```

### Unraid

Install Python/PIP using either:
- Nerd-tools Plugin (Unraid 6)
- Python 3 for UNRAID Plugin (Unraid 6 or 7)
- Manual installation via command line

Install as root (**NOT** recommended):
```bash
pip install deemon
deemon --init
```

If deemon is not found in your path, call it as a python module:
```bash
python3 -m deemon --init
```

When installed as root, the config.json will be located at: **/root/.config/deemon/config.json**.

### Installation in a Python Virtual Environment (venv)

```bash
$ python -m venv venv
$ source ./venv/bin/activate
$ pip install deemon
```

When finished:
```bash
$ deactivate
```

Next time you want to run deemon:
```bash
$ source ./venv/bin/activate
$ deemon refresh
```

## Configuration

### Initial Setup

After installation, initialize deemon:
```bash
deemon --init
```

This creates the configuration directory and database.

### ARL Token

For downloading music, you need a Deezer ARL token:

1. Get your ARL token from the [deemix documentation](https://codeberg.org/RemixDev/deemix-pyweb/src/branch/master/docs/arl.md)
2. Set it in deemon:
```bash
deemon --arl YOUR_ARL_TOKEN_HERE
```

Or edit `config.json` directly:
```json
{
  "deemix": {
    "arl": "YOUR_192_CHARACTER_ARL_TOKEN"
  }
}
```

### Configuration File Location

- **macOS/Linux**: `~/.config/deemon/config.json`
- **Windows**: `%APPDATA%\deemon\config.json`

### Configuration Options

#### Global Settings

```json
{
  "global": {
    "bitrate": "320",
    "alerts": false,
    "record_type": "all",
    "download_path": "",
    "email": ""
  }
}
```

- **bitrate**: Audio quality - "128" (MP3 128kbps), "320" (MP3 320kbps), "FLAC" (lossless)
- **alerts**: Enable email notifications for new releases
- **record_type**: "all", "album", "ep", or "single"
- **download_path**: Custom download directory (empty = default)
- **email**: Email address for notifications

#### Deezer Settings

```json
{
  "deemix": {
    "path": "",
    "arl": "",
    "check_account_status": true,
    "halt_download_on_error": false
  }
}
```

- **path**: Path to deemix installation (auto-detected if empty)
- **arl**: Deezer ARL token (192 characters)
- **check_account_status**: Verify Deezer account status
- **halt_download_on_error**: Stop all downloads if one fails

#### Exclusions

```json
{
  "exclusions": {
    "enable_exclusions": true,
    "patterns": [],
    "keywords": []
  }
}
```

- **enable_exclusions**: Enable exclusion filters
- **patterns**: Regex patterns to exclude albums (e.g., `["Live.*", "Remastered"]`)
- **keywords**: Keywords in parentheses to exclude (e.g., `["Live", "Demo"]`)

#### New Releases

```json
{
  "new_releases": {
    "release_max_age": 90,
    "include_unofficial": false,
    "include_compilations": false,
    "include_featured_in": false
  }
}
```

- **release_max_age**: Maximum age (days) to consider as "new"
- **include_unofficial**: Include unofficial releases
- **include_compilations**: Include compilation albums
- **include_featured_in**: Include albums where artist is featured

#### Email Notifications (SMTP)

```json
{
  "smtp_settings": {
    "server": "smtp.gmail.com",
    "port": 465,
    "starttls": false,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_addr": "your-email@gmail.com"
  }
}
```

- **server**: SMTP server address
- **port**: SMTP port (465 for SSL, 587 for STARTTLS)
- **starttls**: Use STARTTLS instead of SSL
- **username**: SMTP username
- **password**: SMTP password (use app passwords for Gmail)
- **from_addr**: From email address

#### Plex Integration

```json
{
  "plex": {
    "base_url": "http://localhost:32400",
    "ssl_verify": true,
    "token": "YOUR_PLEX_TOKEN",
    "library": "Music"
  }
}
```

- **base_url**: Plex server URL
- **ssl_verify**: Verify SSL certificate
- **token**: Plex authentication token
- **library**: Name of music library

#### Advanced Settings

```json
{
  "check_update": 1,
  "debug_mode": false,
  "release_channel": "stable",
  "query_limit": 5,
  "smart_search": true,
  "rollback_view_limit": 10,
  "prompt_duplicates": false,
  "prompt_no_matches": true,
  "fast_api": true,
  "fast_api_threads": 25
}
```

- **check_update**: Days between update checks
- **debug_mode**: Enable debug logging
- **release_channel**: "stable" or "beta"
- **query_limit**: Max artist search results
- **smart_search**: Use fuzzy matching for artist search
- **rollback_view_limit**: Number of transactions to show
- **prompt_duplicates**: Ask before adding duplicate artists
- **prompt_no_matches**: Ask when no artists found
- **fast_api**: Enable fast API mode
- **fast_api_threads**: Number of threads for fast API

## Commands

### Overview

deemon provides both interactive menu mode and command-line interface.

**Interactive Mode:**
```bash
deemon
```

Press `h` in the menu to show a cheatsheet!

**Command-Line Mode:**
```bash
deemon COMMAND [OPTIONS] [ARGUMENTS]
deemon cheatsheet  # Show quick reference
```

### Available Commands

#### `download` - Download music

Download specific artists, albums, tracks, or by URL.

```bash
deemon download [OPTIONS] [ARTIST...]
```

**Options:**
- `--band BAND`: Band/Artist name (use with --album)
- `--album ALBUM`: Album name (use with --band)
- `-m, --monitored`: Download all currently monitored artists
- `-i, --artist-id ID`: Download by artist ID (multiple)
- `-A, --album-id ID`: Download by album ID (multiple)
- `-T, --track-id ID`: Download by track ID (multiple)
- `-u, --url URL`: Download by URL (multiple)
- `--artist-file FILE`: Download batch of artists from file
- `--album-file FILE`: Download batch of albums from file
- `--track-file FILE`: Download batch of tracks from file
- `-a, --after YYYY-MM-DD`: Grab releases after this date
- `-B, --before YYYY-MM-DD`: Grab releases before this date
- `-b, --bitrate BITRATE`: Set custom bitrate (1=128, 3=320, 9=FLAC)
- `-o, --download-path PATH`: Specify custom download directory
- `-t, --record-type TYPE`: Filter by record type (all/album/ep/single)

**Examples:**
```bash
# Download artist - album (positional)
deemon download "Slayer - South of Heaven"

# Download using --band and --album flags (great for Keyboard Maestro!)
deemon download --band "Slayer" --album "South of Heaven"

# Download artist by name
deemon download Mozart

# Download by artist ID
deemon download -i 27 -i 1

# Download by album ID with FLAC quality
deemon download -A 103248 -b 9

# Download by URL
deemon download -u https://www.deezer.com/album/103248
deemon download --url "https://www.deezer.com/album/103248"  # Long form

# Download multiple artists
deemon download Mozart Beethoven Bach

# Download monitored artists
deemon download -m

# Download with date range
deemon download Mozart -a 2020-01-01 -B 2020-12-31

# Download from file
deemon download --artist-file artists.txt
```

#### `playlist` - Download playlists

Download full playlists from Spotify or Deezer.

```bash
deemon playlist URL [OPTIONS]
```

**Options:**
- `-c, --collection-matcher`: Skip existing tracks (use collection matcher)

**Examples:**
```bash
# Download playlist
deemon playlist "https://www.deezer.com/playlist/123456"

# Download playlist skipping existing tracks
deemon playlist -c "https://www.deezer.com/playlist/123456"
```

#### `global` - Quick download by URL

Quick download by Spotify/Deezer URL (track, album, playlist, or artist).

```bash
deemon global URL
```

**Examples:**
```bash
deemon global "https://www.deezer.com/album/103248"
```

#### `discography` - Download artist discography

Download full discography for an artist (identified by album).

```bash
deemon discography [OPTIONS]
```

**Options:**
- `-b, --band BAND`: Band or artist name
- `-a, --album ALBUM`: Album name to identify artist
- `--include-singles`: Include singles in discography
- `--print-only`: Print album URLs instead of downloading

**Examples:**
```bash
deemon discography -b "Slayer" -a "South of Heaven"
```

#### `monitor` - Monitor artists

Monitor artists for new releases.

```bash
deemon monitor [OPTIONS] [ARTIST...]
```

**Options:**
- `-a, --alerts`: Enable alerts for this monitoring
- `-b, --bitrate BITRATE`: Set custom bitrate
- `-D, --download`: Download all releases matching record type
- `-d, --download-path PATH`: Specify custom download directory
- `-I, --import PATH`: Import artists/IDs from file or directory
- `-i, --artist-id`: Monitor artist by ID
- `-p, --playlist`: Monitor Deezer playlist by URL
- `--include-artists`: Also monitor artists from playlist
- `-u, --url`: Monitor artist by URL
- `-R, --remove`: Stop monitoring an artist
- `-s, --search`: Show similar artist results to choose from
- `-T, --time-machine DATE`: Refresh as if it were this date (YYYY-MM-DD)
- `-t, --record-type TYPE`: Specify record types to download

**Examples:**
```bash
# Monitor artist by name
deemon monitor Mozart

# Monitor by artist ID
deemon monitor -i 27

# Monitor by URL
deemon monitor -u https://www.deezer.com/us/artist/27

# Monitor playlist
deemon monitor -p https://www.deezer.com/us/playlist/908622995

# Monitor playlist and include artists
deemon monitor -p https://www.deezer.com/us/playlist/908622995 --include-artists

# Import from file
deemon monitor -I artists.txt

# Search and select artist
deemon monitor -s Mozart

# Stop monitoring artist
deemon monitor -R Mozart

# Monitor with custom settings
deemon monitor Mozart -b 9 -t album -D
```

#### `refresh` - Check for new releases

Check monitored artists for new releases.

```bash
deemon refresh [OPTIONS] [NAME...]
```

**Options:**
- `-p, --playlist`: Refresh a specific playlist by name
- `-s, --skip-download`: Skip downloading new releases
- `-T, --time-machine DATE`: Refresh as if it were this date (YYYY-MM-DD)

**Examples:**
```bash
# Refresh all monitored artists
deemon refresh

# Refresh specific artist
deemon refresh Mozart

# Refresh specific playlist
deemon refresh -p "My Playlist"

# Refresh without downloading
deemon refresh -s

# Time machine refresh
deemon refresh -T 2020-01-01
```

#### `show` - Show monitored artists and releases

Display monitored artists, playlists, and recent releases.

```bash
deemon show COMMAND [OPTIONS] [ARGUMENTS]
```

**Subcommands:**

`show artists` - Show monitored artists
```bash
deemon show artists [OPTIONS] [ARTIST]
```
Options:
- `-c, --csv`: Output as CSV
- `-e, --export PATH`: Export CSV to file
- `-f, --filter FILTER`: Filter CSV output
- `-H, --hide-header`: Hide header on CSV
- `-b, --backup PATH`: Backup artist IDs to CSV

`show playlists` - Show monitored playlists
```bash
deemon show playlists [OPTIONS] [TITLE]
```
Options:
- `-c, --csv`: Output as CSV
- `-f, --filter FILTER`: Filter CSV output
- `-H, --hide-header`: Hide header on CSV
- `-i, --playlist-id`: Show by playlist ID

`show releases` - Show recent or future releases
```bash
deemon show releases [OPTIONS] [DAYS]
```
Options:
- `-f, --future`: Display future releases

**Examples:**
```bash
# Show all monitored artists
deemon show artists

# Show specific artist
deemon show artists Mozart

# Export artists to CSV
deemon show artists -e artists.csv

# Show releases in last 7 days
deemon show releases

# Show releases in last 30 days
deemon show releases 30

# Show upcoming releases
deemon show releases -f

# Show monitored playlists
deemon show playlists
```

#### `search` - Search and download/monitor

Interactively search for artists and choose to download or monitor.

```bash
deemon search [QUERY]
```

**Examples:**
```bash
# Interactive search
deemon search

# Search with query
deemon search Mozart
```

#### `config` - Configure per-artist settings

Set custom configuration for specific artists.

```bash
deemon config ARTIST
```

**Examples:**
```bash
deemon config Mozart
```

#### `global` - Quick download by URL

Quick download without monitoring.

```bash
deemon global [OPTIONS] [URL...]
```

**Options:**
- `-b, --bitrate BITRATE`: Set custom bitrate
- `-o, --download-path PATH`: Specify custom download directory

**Examples:**
```bash
# Download album by URL
deemon global https://www.deezer.com/album/103248

# Download track by URL with FLAC
deemon global https://www.deezer.com/track/3135556 -b 9

# Download playlist
deemon global https://www.deezer.com/playlist/908622995
```

#### `backup` - Backup/restore configuration

Backup configuration and database to a tar file.

```bash
deemon backup [OPTIONS]
```

**Options:**
- `-i, --include-logs`: Include log files in backup
- `-r, --restore`: Restore from existing backup

**Examples:**
```bash
# Create backup
deemon backup

# Create backup with logs
deemon backup -i

# Restore from backup
deemon backup -r
```

#### `profile` - Manage configuration profiles

Add, modify, and delete configuration profiles.

```bash
deemon profile [PROFILE] [OPTIONS]
```

**Options:**
- `-a, --add`: Add new profile
- `-c, --clear`: Clear config for existing profile
- `-d, --delete`: Delete an existing profile
- `-e, --edit`: Edit an existing profile

**Examples:**
```bash
# Show all profiles
deemon profile

# Create new profile
deemon profile my-profile -a

# Edit profile
deemon profile my-profile -e

# Delete profile
deemon profile my-profile -d

# Clear profile config
deemon profile my-profile -c
```

#### `rollback` - Rollback transactions

Rollback a previous monitor or refresh transaction.

```bash
deemon rollback [OPTIONS] [NUM]
```

**Options:**
- `-v, --view`: View recent refresh transactions

**Examples:**
```bash
# View recent transactions
deemon rollback -v

# Rollback last transaction
deemon rollback 1

# Rollback last 3 transactions
deemon rollback 3
```

#### `test` - Test configuration

Run tests on email configuration, exclusion filters, etc.

```bash
deemon test [OPTIONS]
```

**Options:**
- `-e, --email`: Send test notification to configured email
- `-E, --exclusions URL`: Test exclude regex pattern against URL

**Examples:**
```bash
# Test email notification
deemon test -e

# Test exclusion pattern
deemon test -E "Album Name (Live)"
```

#### `reset` - Reset database

Reset monitoring database (removes all artists and playlists).

```bash
deemon reset
```

**Warning:** This will remove all monitored artists and playlists regardless of profile!

#### `discography` - Download full discography

Download or list an artist's full discography.

```bash
deemon discography [OPTIONS]
```

**Options:**
- `-b, --band BAND`: Band or artist name
- `-a, --album ALBUM`: Album name to identify artist
- `--include-singles`: Include singles in discography
- `--print-only`: Print album URLs instead of queueing downloads

**Examples:**
```bash
# Download full discography
deemon discography -b "Radiohead" -a "OK Computer"

# Download including singles
deemon discography -b "Radiohead" -a "OK Computer" --include-singles

# Print album URLs only
deemon discography -b "Radiohead" -a "OK Computer" --print-only

# Interactive input
deemon discography
# Then enter: Radiohead - OK Computer
```

#### `library` - Library management

Library-related commands (upgrade, output, etc.).

```bash
deemon library [OPTIONS]
```

**Subcommands:**
- `upgrade`: Upgrade library entries

#### `extra` - Fetch extra release info

Fetch additional release information.

```bash
deemon extra
```

### Global Options

- `-h, --help`: Show help message
- `-V, --version`: Show version
- `-v, --verbose`: Show debug output
- `--init`: Initialize deemon application data directory
- `--arl ARL`: Update ARL token
- `-P, --profile PROFILE`: Run deemon with specific profile
- `--whats-new`: Show release notes from current version

## Examples

### Basic Workflow

```bash
# 1. Initialize deemon
deemon --init

# 2. Set ARL token
deemon --arl YOUR_192_CHAR_ARL_TOKEN

# 3. Monitor some artists
deemon monitor Mozart Beethoven Bach

# 4. Check for new releases
deemon refresh

# 5. View monitored artists
deemon show artists

# 6. View recent releases
deemon show releases
```

### Download Specific Albums

```bash
# Download by URL
deemon download -u https://www.deezer.com/album/103248

# Download by album ID with FLAC
deemon download -A 103248 -b 9

# Download multiple albums
deemon download -A 103248 -A 123456 -A 789012
```

### Monitor and Download Automatically

```bash
# Monitor artists with auto-download
deemon monitor Mozart -D -b 9 -t album

# Monitor playlist with auto-download
deemon monitor -p https://www.deezer.com/playlist/908622995 --include-artists -D

# Refresh and download new releases
deemon refresh
```

### Batch Operations

```bash
# Import artists from file (one per line)
deemon monitor -I artists.txt

# Download albums from file
deemon download --album-file albums.txt

# Export monitored artists to CSV
deemon show artists -e backup.csv
```

### Use with Profiles

```bash
# Create profile for high-quality downloads
deemon profile hq -a
# Configure bitrate to FLAC, record_type to album

# Monitor using profile
deemon -P hq monitor Mozart

# Refresh using profile
deemon -P hq refresh
```

### Time Machine

```bash
# Monitor artists as if it were 2020-01-01
deemon monitor Mozart -T 2020-01-01

# Refresh as if it were 2020-01-01
deemon refresh -T 2020-01-01
```

### Exclusion Filters

Configure in `config.json`:
```json
{
  "exclusions": {
    "enable_exclusions": true,
    "patterns": ["Live.*", "Remastered.*", "Deluxe.*"],
    "keywords": ["Live", "Demo", "Remix"]
  }
}
```

Test exclusion:
```bash
deemon test -E "Album Name (Live)"
```

### Email Notifications

Configure SMTP in `config.json`:
```json
{
  "smtp_settings": {
    "server": "smtp.gmail.com",
    "port": 465,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_addr": "your-email@gmail.com"
  },
  "global": {
    "alerts": true,
    "email": "your-email@gmail.com"
  }
}
```

Test email:
```bash
deemon test -e
```

### Playlist Monitoring

```bash
# Monitor Spotify playlist
deemon monitor -p https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

# Monitor Deezer playlist
deemon monitor -p https://www.deezer.com/us/playlist/908622995

# Monitor playlist and include all artists
deemon monitor -p https://www.deezer.com/us/playlist/908622995 --include-artists
```

### Discography Download

```bash
# Download full discography
deemon discography -b "Pink Floyd" -a "The Dark Side of the Moon" --include-singles

# Print album URLs instead of downloading
deemon discography -b "Pink Floyd" -a "The Dark Side of the Moon" --print-only
```

## Automation

### Cron (Linux/macOS)

Add to crontab (`crontab -e`):

```bash
# Check for new releases every day at 2 AM
0 2 * * * /usr/local/bin/deemon refresh

# Check for new releases every 6 hours
0 */6 * * * /usr/local/bin/deemon refresh
```

### Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily)
4. Set action: `python3 -m deemon refresh`
5. Configure additional settings as needed

### Docker with Cron

Create a script (`refresh.sh`):
```bash
#!/bin/bash
docker run --name deemon \
       --rm \
       -v /path/to/deemon/config:/config \
       -v /path/to/music:/downloads \
       -v /path/to/deemix/config:/deemix  \
       ghcr.io/digitalec/deemon:latest \
       python3 -m deemon refresh
```

Add to crontab:
```bash
0 2 * * * /path/to/refresh.sh
```

## Troubleshooting

### Common Issues

**"Possible invalid ARL detected"**
- ARL should be exactly 192 characters
- Re-generate your ARL token from Deezer

**"No releases found matching applied filters"**
- Check your `record_type` setting in config
- Verify exclusion filters aren't blocking releases
- Try `deemon download -t all` to download all release types

**Download errors**
- Check deemix configuration
- Verify ARL token is valid
- Check internet connection
- Review logs at `~/.local/share/deemon/deemon.log`

**Artists not being monitored**
- Use `deemon show artists` to verify
- Check for typos in artist names
- Try `deemon monitor -s ARTIST` to search and select

**Email notifications not working**
- Verify SMTP settings in config
- Test with `deemon test -e`
- Check firewall/network settings
- Use app-specific passwords for Gmail

**Database errors**
- Reset with `deemon reset` (warning: removes all data)
- Restore from backup: `deemon backup -r`
- Check file permissions

### Logs

Log location:
- **macOS/Linux**: `~/.local/share/deemon/deemon.log`
- **Windows**: `%APPDATA%\Local\deemon\deemon.log`

Enable debug mode in `config.json`:
```json
{
  "debug_mode": true
}
```

Or use command line:
```bash
deemon -v refresh
```

### Getting Help

- Check documentation: https://digitalec.github.io/deemon
- Open an issue: https://github.com/digitalec/deemon/issues/new
- Join Discord: https://discord.gg/KzNCG2tkvn

## License

GPL3 - See LICENSE file for details

## Contributing

Contributions are welcome! Please visit:
- GitHub: https://github.com/digitalec/deemon
- Issues: https://github.com/digitalec/deemon/issues

## Acknowledgments

- deemix - Download engine
- Deezer API - Music data source
- Click - CLI framework
- All contributors and users
