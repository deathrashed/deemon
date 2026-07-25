# deemon MCP Server

Music monitoring and downloader MCP server — searches Deezer, downloads albums/tracks, and manages monitored artists.

## Tools

| Tool | Description |
|------|-------------|
| `search_artists` | Search Deezer for artists |
| `get_artist_albums` | Get all releases for an artist |
| `get_album_info` | Get details for a specific album |
| `download_url` | Download from a Deezer/Spotify URL |
| `download_album` | Download album by Deezer album ID |
| `download_album_by_name` | Search artist + album name and download |
| `download_track` | Download track by Deezer track ID |
| `monitor_artist` | Start monitoring an artist for new releases |
| `list_monitored_artists` | List all monitored artists |
| `list_recent_releases` | Recent new releases from monitored artists |

## Connection

### opencode

Add to `~/.config/opencode/opencode.json`:

```json
"deemon": {
  "type": "local",
  "command": [
    "/Users/rd/Scripts/Riley/audio/download/deemon/.venv/bin/python",
    "-u",
    "/Users/rd/Scripts/Riley/audio/download/deemon/deemon_mcp.py"
  ],
  "enabled": true
}
```

### Claude Code

The `.mcp.json` in this folder provides the config — point your Claude Code project at this directory or merge the entry into your global `claude_desktop_config.json`.

### Any MCP client

```
command: /Users/rd/Scripts/Riley/audio/download/deemon/.venv/bin/python
args: [-u, /Users/rd/Scripts/Riley/audio/download/deemon/deemon_mcp.py]
```

## Requirements

- Python 3.10+
- The deemon package installed in the `.venv` (run `./install.sh` or `pip install -e .` in the project root)
- Deezer ARL token in `~/.config/deemon/config.json`
