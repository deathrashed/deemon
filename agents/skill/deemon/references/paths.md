# deemon Paths Reference

## Project

| What | Path |
|------|------|
| Project root | `/Users/rd/Scripts/Riley/audio/download/deemon` |
| Venv Python | `/Users/rd/Scripts/Riley/audio/download/deemon/.venv/bin/python` |
| Venv deemon CLI | `/Users/rd/Scripts/Riley/audio/download/deemon/.venv/bin/deemon` |
| MCP server | `/Users/rd/Scripts/Riley/audio/download/deemon/deemon_mcp.py` |
| Raycast bridge | `/Users/rd/Scripts/Riley/audio/download/deemon/raycast_bridge.py` |
| Deemix config | `/Users/rd/Scripts/Riley/audio/download/deemon/config/config.json` |
| Spotify creds | `/Users/rd/Scripts/Riley/audio/download/deemon/config/spotify/config.json` |
| Dockerfile | `/Users/rd/Scripts/Riley/audio/download/deemon/Dockerfile` |
| Install script | `/Users/rd/Scripts/Riley/audio/download/deemon/install.sh` |

## Runtime (macOS)

| What | Path |
|------|------|
| deemon config | `~/Library/Application Support/deemon/config.json` |
| deemon database | `~/Library/Application Support/deemon/deemon.db` |
| Backup config | `/etc/xdg/deemon/config.json` (fallback) |
| XDG override | `$XDG_CONFIG_HOME/deemon/config.json` |

## Skill

| What | Path |
|------|------|
| Skill root | `/Users/rd/Scripts/Riley/audio/download/deemon/agents/skill/deemon/` |
| Symlink target | `/Users/rd/.agents/skills/deemon` → points to skill root |
| SKILL.md | `agents/skill/deemon/SKILL.md` |
| References | `agents/skill/deemon/references/` |
| Scripts | `agents/skill/deemon/scripts/` |

## MCP

| What | Path |
|------|------|
| MCP config | `/Users/rd/Scripts/Riley/audio/download/deemon/agents/mcp/.mcp.json` |
| MCP README | `/Users/rd/Scripts/Riley/audio/download/deemon/agents/mcp/README.md` |
| Global MCP entry | `/Users/rd/.config/opencode/opencode.json` (key: `deemon`) |
| MCP server script | `/Users/rd/Scripts/Riley/audio/download/deemon/deemon_mcp.py` |

## Key Source Files

| What | Path |
|------|------|
| CLI entry point | `deemon/__main__.py` |
| CLI commands | `deemon/cli.py` |
| Config manager | `deemon/core/config.py` |
| Database manager | `deemon/core/db.py` |
| Deezer API | `deemon/core/api.py` |
| Deemix interface | `deemon/core/dmi.py` |
| Download logic | `deemon/cmd/download.py` |
| Monitor logic | `deemon/cmd/monitor.py` |
| Refresh logic | `deemon/cmd/refresh.py` |
| Notifications | `deemon/core/notifier.py` |
| Collection matcher | `deemon/core/rileys_collection_matcher.py` |
| Spotify plugin | `deemon/plugins/spotify.py` |
