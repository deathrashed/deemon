# deemon Paths Reference

Set `DEEMON_ROOT` to the absolute path of the cloned repository. Paths below are portable examples, not values to commit into a client configuration.

## Project

| What | Path |
|------|------|
| Project root | `$DEEMON_ROOT` |
| Venv Python | `$DEEMON_ROOT/.venv/bin/python` |
| Venv deemon CLI | `$DEEMON_ROOT/.venv/bin/deemon` |
| MCP server | `$DEEMON_ROOT/scripts/deemon-mcp.py` |
| Raycast bridge | `$DEEMON_ROOT/scripts/raycast-bridge.py` |
| Deemix config | `~/.config/deemix/config.json` or `~/Library/Application Support/deemix/config.json` |
| Spotify credentials | deemon application config via `deemon settings` |
| Dockerfile | `$DEEMON_ROOT/Dockerfile` |
| Install script | `$DEEMON_ROOT/install.sh` |

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
| Skill root | `$DEEMON_ROOT/agents/skill/deemon/` |
| Symlink target | user-specific agent skill location → points to skill root |
| SKILL.md | `agents/skill/deemon/SKILL.md` |
| References | `agents/skill/deemon/references/` |
| Scripts | `agents/skill/deemon/scripts/` |

## MCP

| What | Path |
|------|------|
| MCP config | `$DEEMON_ROOT/agents/mcp/.mcp.json` |
| MCP README | `$DEEMON_ROOT/agents/mcp/README.md` |
| Global MCP entry | your MCP client's configuration file (key: `deemon`) |
| MCP server script | `$DEEMON_ROOT/scripts/deemon-mcp.py` |

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
