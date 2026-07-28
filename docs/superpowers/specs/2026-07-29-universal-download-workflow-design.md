# Universal Download Workflow Design

## Goal

Make deemon's existing interactive TUI, CLI, Raycast commands, Keyboard Maestro macros, MCP server, and scheduled scripts use one dependable download workflow. A user can provide a Deezer URL or ID, a Spotify URL, an artist/album query, or a supported text file; deemon resolves it into Deezer URL(s), presents a plan when requested, and queues it through the existing downloader.

## Product Rules

1. Deezer is the canonical download source. All completed resolution returns Deezer URLs or IDs.
2. Spotify is an optional input format, never a requirement for core downloads.
3. Individual Spotify artist, album, and track links must resolve automatically without configured Spotify credentials when a safe match can be made.
4. Spotify playlists require configured Spotify access for enumeration. Deemon must explain that requirement before doing any work.
5. The TUI remains the visual front end. It must delegate to the same application-level operations as CLI commands.
6. Every non-destructive, useful action exposed in the TUI has a non-interactive CLI equivalent. Machine-readable output is opt-in with `--json`.
7. Existing command names remain functional; `deemon get` is the concise primary entry point for new users and integrations.

## User Interfaces

### Primary command

```text
deemon get INPUT [--dry-run] [--json] [--yes] [--collection-matcher]
```

`INPUT` accepts one URL, a Deezer ID with an explicit type flag, an `Artist - Album` query, an artist query, or a readable supported file path. The command detects the input kind, resolves it, returns a plan for `--dry-run`, asks for confirmation when interactive, and queues it when `--yes` is present.

### Supporting commands

```text
deemon resolve INPUT [--json]
deemon queue list [--json]
deemon queue retry [--failed] [--yes]
deemon doctor [--json]
```

Existing `download`, `playlist`, and `discography` commands delegate to the same resolver and queue planner. Future command work provides non-interactive config/profile mutation and explicit backup restore paths.

### TUI

The current ANSI/keyboard-oriented TUI styling remains intact. Its Download menu gains a single "Paste or type anything" entry that invokes the shared intake operation. The home screen displays active profile, Deezer readiness, download path, queue count, and Spotify resolver capability. Existing detailed menus remain available.

## Resolution Pipeline

```text
input
  -> classify
  -> resolve source metadata
  -> match Deezer entity
  -> return Deezer URL(s) + confidence + provenance
  -> build download plan
  -> confirm or queue
  -> existing deemix downloader
```

### Classification

- Deezer URL/ID: validate and pass through.
- Spotify artist/album/track URL: use configured Spotify metadata first; otherwise use Spotify's public oEmbed metadata and Deezer search.
- Spotify playlist URL: use configured Spotify metadata only; otherwise return a structured capability error.
- Artist/album text: reuse existing Deezer search and existing ambiguity handling.
- File: reuse `--artist-file`, `--album-file`, and `--track-file` parsers after determining its supported format.

### Matching

Prefer exact UPC/ISRC identity. Fall back to normalized artist/title comparison, release year, and track count where available. Auto-select only high-confidence matches. Interactive TUI shows candidates for ambiguous matches; `--json` returns candidates and a nonzero status without downloading.

## Automation Contract

- Human-readable output remains default.
- `--json` emits a stable envelope with `status`, `input`, `resolved`, `plan`, `warnings`, and `errors`.
- `--dry-run` performs no queueing or download.
- `--yes` permits queueing only after a non-empty plan has been produced; destructive operations retain their explicit confirmation requirements.
- All resolver errors are actionable and classify missing capability, invalid input, no match, ambiguous match, and download failure separately.

## Integration Migration

Raycast scripts and Keyboard Maestro macros must invoke stable `deemon` commands instead of duplicating Spotify metadata logic or embedding repository paths. Use the installed CLI location or a single maintained wrapper. Update stale `Audio/Acquisition/deemon` references to the maintained launcher contract.

MCP tools reuse the resolver and queue planner, returning structured plans or results rather than independently calling download internals.

## Delivery Order

1. Resolver model and `resolve` command, with direct Deezer and Spotify individual-link fallback.
2. `get` command, plan output, `--dry-run`, `--json`, and `--yes`.
3. Queue inspection/retry and doctor command.
4. TUI Download-Hub integration and status indicators.
5. Raycast, Keyboard Maestro, and MCP migration.
6. Remaining TUI-to-CLI parity: configuration/profile mutation, restore path selection, and search result selection.

## Validation

- Unit tests for classification, confidence rules, and JSON envelopes.
- CLI smoke tests for help, dry-run, JSON, direct Deezer inputs, text inputs, files, and Spotify fallback failure modes.
- Manual TUI run through the new intake item and an existing detailed download route.
- Raycast/macro command inspection and a no-download dry-run where their host applications are available.
- No test can use real credentials or trigger a download by default.

## Scope Boundaries

This work does not replace deemix, scrape Spotify pages, add a second TUI framework, or make Spotify playlist expansion work without a supported metadata capability. It preserves existing CLI commands and focuses on one shared intake/resolution path.
