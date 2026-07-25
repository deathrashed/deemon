# deemon Agent Skill — Design Doc

## Purpose

Create a self-contained agent skill for deemon that lets any agent (OpenCode, Claude Code, etc.) work with the deemon music monitoring and downloader — via its CLI, MCP server, and raw database/config access — without needing to read the project source.

## Architecture

### Canonical location

```
/Users/rd/Scripts/Riley/audio/download/deemon/agents/skill/deemon/
├── SKILL.md               # Entry point: cheatsheet + MCP ref + when-to-use
├── references/
│   ├── commands.md        # Full CLI reference with all flags and examples
│   ├── config.md          # Config schema with defaults and field descriptions
│   ├── database.md        # DB schema, tables, columns, useful queries
│   └── paths.md           # All important file paths (project + runtime)
└── scripts/
    ├── deemon-check.sh    # Health check: venv, ARL, config, DB, deemix
    └── deemon-query.sh    # Read-only SQL query runner for deemon.db
```

### Symlink

`/Users/rd/.agents/skills/deemon` → `/Users/rd/Scripts/Riley/audio/download/deemon/agents/skill/deemon/`

This mirrors the established pattern in `.agents/skills/` where most skills are symlinks to canonical sources in `.cc-switch/skills/` or `ai/store/skills/`.

### MCP companion

`/Users/rd/Scripts/Riley/audio/download/deemon/agents/mcp/` — contains `.mcp.json` and `README.md` for the deemon MCP server. Agents can use either the CLI (for downloads/monitoring) or the MCP (for structured queries).

## Components

### SKILL.md
- Frontmatter with triggers for automatic skill invocation
- CLI quick reference (cheatsheet)
- MCP tool table
- Guidance on CLI vs MCP trade-offs
- Pointers to reference files and scripts

### Reference files
- **commands.md** — 1:1 mapping of every deemon subcommand, option, and example
- **config.md** — full default config JSON with per-field annotations
- **database.md** — all 7 tables with columns, types, and useful SQL queries
- **paths.md** — absolute paths for project root, venv, config, DB, source files, MCP, symlink

### Scripts
- **deemon-check.sh** — agent-friendly health check that prints: venv status, CLI version, ARL presence, bitrate setting, DB path/size/monitored count, deemix config status
- **deemon-query.sh** — `deemon-query.sh 'SELECT ...'` runs read-only SQL against deemon.db and formats results as a table

## Design Decisions

1. **References as separate files, not embedded in SKILL.md** — keeps SKILL.md concise and focused on the cheatsheet. Agents can read individual reference files on demand.

2. **Helpers as shell scripts, not Python** — zero dependency overhead. The health check and query script only need Python (which deemon already requires) and standard Unix tools.

3. **Symlink to the folder, not individual files** — the folder can grow with more references, scripts, or assets without changing the symlink.

4. **Co-located with the project** — the skill lives inside the deemon repo so it stays versioned alongside the code it documents. Changes to deemon's CLI or config schema are naturally reflected in the skill.

## Future Additions

- `references/examples.md` — common workflows and recipes
- `scripts/deemon-debug.sh` — collect logs, config dump, DB dump for debugging
- `scripts/deemon-batch.sh` — batch download from a text file with progress
