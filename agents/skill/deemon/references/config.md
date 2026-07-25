# deemon Config Reference

Config file: `~/Library/Application Support/deemon/config.json` (macOS) or `~/.config/deemon/config.json` (Linux)

## Default Config

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
  "fast_api_threads": 25,

  "exclusions": {
    "enable_exclusions": true,
    "patterns": [],
    "keywords": []
  },

  "new_releases": {
    "release_max_age": 90,
    "include_unofficial": false,
    "include_compilations": false,
    "include_featured_in": false
  },

  "global": {
    "bitrate": "320",
    "alerts": false,
    "record_type": "all",
    "download_path": "",
    "email": ""
  },

  "deemix": {
    "path": "",
    "arl": "",
    "check_account_status": true,
    "halt_download_on_error": false
  },

  "smtp_settings": {
    "server": "",
    "port": 465,
    "starttls": false,
    "username": "",
    "password": "",
    "from_addr": ""
  },

  "plex": {
    "base_url": "",
    "ssl_verify": true,
    "token": "",
    "library": ""
  }
}
```

## Key Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `global.bitrate` | string | `"320"` | `128`, `320`, or `FLAC` |
| `global.record_type` | string | `"all"` | `all`, `album`, `ep`, `single` |
| `global.alerts` | bool | `false` | Enable email notifications |
| `global.download_path` | string | `""` | Custom download directory |
| `deemix.arl` | string | `""` | Deezer ARL token (192 chars) |
| `fast_api` | bool | `true` | Use Deezer GW API (faster) |
| `fast_api_threads` | int | `25` | GW API threads (max 50) |
| `exclusions.patterns` | array | `[]` | Regex patterns to exclude |
| `exclusions.keywords` | array | `[]` | Keywords to exclude |
| `new_releases.release_max_age` | int | `90` | Max days for new releases |
| `plex.base_url` | string | `""` | Plex server URL |
| `smtp_settings.server` | string | `""` | SMTP server for alerts |

## CLI Flag Mappings

| CLI flag | Config field |
|----------|-------------|
| `-b, --bitrate N` | `global.bitrate` (1=128, 3=320, 9=FLAC) |
| `-o, --download-path PATH` | `global.download_path` |
| `-t, --record-type TYPE` | `global.record_type` |
| `-v, --verbose` | `debug_mode` |

## Allowed Values

| Setting | Values |
|---------|--------|
| bitrate | `128`, `320`, `FLAC` |
| record_type | `all`, `album`, `ep`, `single` |
| release_channel | `stable`, `beta` |

## Config Migration

The config auto-migrates on load: missing keys are added with defaults, old property names are remapped, and value types are corrected (e.g. `"1"` → `"128"`, `0`/`1` → `false`/`true`).
