# Universal Intake Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a shared, non-destructive resolver and `deemon get`/`deemon resolve` commands that normalize supported inputs into Deezer URLs before the existing download queue runs.

**Architecture:** Create a focused resolver module that classifies inputs, resolves direct Deezer URLs and user text through existing `PlatformAPI` methods, and represents the result as a JSON-serializable plan. The CLI commands only translate options into the resolver/queue calls; the TUI and integrations are deliberately not changed in this phase.

**Tech Stack:** Python 3.10+, Click, requests, deezer-python, existing `PlatformAPI`, existing `Download`/deemix queue.

---

## Scope and file structure

| File | Responsibility |
|---|---|
| `deemon/core/resolver.py` | Input classification, Deezer resolution, confidence and JSON envelope creation. |
| `deemon/cmd/download.py` | Consume already-resolved Deezer URLs without duplicating source detection. |
| `deemon/cli.py` | Add `resolve` and `get`; expose dry-run, JSON, and explicit queue confirmation. |
| `README.md` | Document the new non-interactive workflow and its safety rules. |
| `docs/docs/commands/download.md` | Document supported inputs and automation examples. |

The repository has no tracked test suite. Do not introduce a test framework in this phase. Validate each task with Click help, deterministic local input checks, and dry-run/manual CLI smoke tests that never invoke deemix downloads.

### Task 1: Define resolver result types

**Files:**
- Create: `deemon/core/resolver.py`

- [ ] **Step 1: Add immutable result records and a stable envelope**

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"
    INVALID = "invalid"
    ERROR = "error"


@dataclass(frozen=True)
class ResolvedItem:
    kind: str
    deezer_url: str
    title: str
    artist: str | None = None
    confidence: float = 1.0
    provenance: str = "deezer"


@dataclass(frozen=True)
class Resolution:
    status: ResolutionStatus
    input_value: str
    items: list[ResolvedItem] = field(default_factory=list)
    candidates: list[ResolvedItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "input": self.input_value,
            "resolved": [asdict(item) for item in self.items],
            "candidates": [asdict(item) for item in self.candidates],
            "warnings": self.warnings,
            "errors": self.errors,
        }
```

- [ ] **Step 2: Compile the new module**

Run: `python3 -m py_compile deemon/core/resolver.py`

Expected: exit status `0`.

- [ ] **Step 3: Commit the type contract**

```bash
git add deemon/core/resolver.py
git commit -m "feat: define download resolution results"
```

### Task 2: Resolve direct Deezer inputs and artist-album text

**Files:**
- Modify: `deemon/core/resolver.py`
- Reference: `deemon/core/api.py:68-164`

- [ ] **Step 1: Add a resolver with explicit supported forms**

```python
class InputResolver:
    def __init__(self, active_api=None):
        from deemon.core.api import PlatformAPI
        self.api = active_api or PlatformAPI()

    def resolve(self, value: str) -> Resolution:
        value = value.strip()
        if not value:
            return Resolution(ResolutionStatus.INVALID, value, errors=["Input is empty."])
        if "deezer.com/" in value:
            return self._resolve_deezer_url(value)
        if "spotify.com/" in value or value.startswith("spotify:"):
            return self._resolve_spotify_url(value)
        if " - " in value:
            artist, album = value.split(" - ", 1)
            return self._resolve_artist_album(artist, album)
        return self._resolve_artist(value)
```

Implement `_resolve_deezer_url` with URL parsing that accepts only `artist`, `album`, `track`, and `playlist` numeric identifiers and returns the normalized `https://www.deezer.com/<kind>/<id>` URL. Implement `_resolve_artist_album` using `PlatformAPI.search_artist()` followed by `PlatformAPI.get_artist_albums()`, and return only a single exact normalized artist/title match. Implement `_resolve_artist` using `PlatformAPI.search_artist()` and return one result only when there is one exact normalized match; otherwise populate `candidates` and return `AMBIGUOUS`.

- [ ] **Step 2: Run deterministic local validation**

Run:

```bash
python3 - <<'PY'
from deemon.core.resolver import InputResolver, ResolutionStatus

resolver = InputResolver(active_api=object())
result = resolver._resolve_deezer_url("https://www.deezer.com/album/123?utm=x")
assert result.status == ResolutionStatus.RESOLVED
assert result.items[0].deezer_url == "https://www.deezer.com/album/123"
assert resolver.resolve("  ").status == ResolutionStatus.INVALID
PY
```

Expected: exit status `0`; no network access and no download.

- [ ] **Step 3: Compile the resolver**

Run: `python3 -m py_compile deemon/core/resolver.py`

Expected: exit status `0`.

- [ ] **Step 4: Commit direct Deezer and text resolution**

```bash
git add deemon/core/resolver.py
git commit -m "feat: resolve Deezer and artist album inputs"
```

### Task 3: Add Spotify fallback without configured API credentials

**Files:**
- Modify: `deemon/core/resolver.py`
- Reference: `deemon/cmd/download.py:158-364`

- [ ] **Step 1: Implement safe Spotify capability branching**

```python
def _resolve_spotify_url(self, value: str) -> Resolution:
    kind, identifier = self._parse_spotify_url(value)
    if kind == "playlist" and not self._spotify_credentials_available():
        return Resolution(
            ResolutionStatus.UNSUPPORTED,
            value,
            errors=["Spotify playlists require configured Spotify API access."],
        )
    if self._spotify_credentials_available():
        return self._resolve_spotify_with_api(kind, identifier, value)
    return self._resolve_spotify_with_oembed(kind, value)
```

`_resolve_spotify_with_oembed` must call Spotify's documented `https://open.spotify.com/oembed?url=...` endpoint with a timeout, extract the public title, search Deezer, and return `RESOLVED` only when the Deezer match exceeds the documented confidence threshold. It must never scrape Spotify HTML, invoke deemix, or silently choose an ambiguous result. For an oEmbed failure, return `ERROR` with the HTTP-safe message; for a non-unique Deezer result, return `AMBIGUOUS` with candidates.

- [ ] **Step 2: Exercise the no-credential playlist branch**

Run:

```bash
python3 - <<'PY'
from deemon.core.resolver import InputResolver, ResolutionStatus

class Resolver(InputResolver):
    def _spotify_credentials_available(self):
        return False

result = Resolver(active_api=object()).resolve("https://open.spotify.com/playlist/abc123")
assert result.status == ResolutionStatus.UNSUPPORTED
assert result.errors == ["Spotify playlists require configured Spotify API access."]
PY
```

Expected: exit status `0`; no network access and no download.

- [ ] **Step 3: Compile the resolver**

Run: `python3 -m py_compile deemon/core/resolver.py`

Expected: exit status `0`.

- [ ] **Step 4: Commit Spotify fallback behavior**

```bash
git add deemon/core/resolver.py
git commit -m "feat: add Spotify to Deezer resolution fallback"
```

### Task 4: Expose `deemon resolve`

**Files:**
- Modify: `deemon/cli.py:1437-1560`
- Modify: `deemon/cli.py:1943-1963`

- [ ] **Step 1: Add the read-only command**

```python
@run.command(name="resolve")
@click.argument("input_value", nargs=-1, required=True)
@click.option("--json", "as_json", is_flag=True, help="Output a stable JSON resolution envelope")
def resolve_command(input_value, as_json):
    """Resolve input into Deezer URL(s) without downloading."""
    from deemon.core.resolver import InputResolver, ResolutionStatus
    result = InputResolver().resolve(" ".join(input_value))
    if as_json:
        click.echo(json.dumps(result.to_dict(), ensure_ascii=False))
    else:
        for item in result.items:
            click.echo(item.deezer_url)
        for message in result.errors:
            click.echo(f"Error: {message}", err=True)
    if result.status is not ResolutionStatus.RESOLVED:
        raise click.ClickException("Resolution did not produce one safe Deezer result.")
```

Add the required `json` import next to the existing standard-library imports. Do not call `Download` from this command.

- [ ] **Step 2: Verify command registration and direct Deezer output**

Run:

```bash
python3 -m deemon resolve --help
python3 -m deemon resolve --json https://www.deezer.com/album/123
```

Expected: help lists `--json`; the second command prints one JSON object with `status` set to `resolved` and does not invoke a download.

- [ ] **Step 3: Compile CLI code**

Run: `python3 -m py_compile deemon/cli.py deemon/core/resolver.py`

Expected: exit status `0`.

- [ ] **Step 4: Commit the resolver CLI**

```bash
git add deemon/cli.py deemon/core/resolver.py
git commit -m "feat: expose input resolution command"
```

### Task 5: Add `deemon get` as a safe intake command

**Files:**
- Modify: `deemon/cli.py:1560-1665`
- Modify: `deemon/cmd/download.py:416-516`

- [ ] **Step 1: Extract a queue method for resolved URLs**

```python
def queue_resolved_urls(self, urls: list[str]) -> list[QueueItem]:
    self.queue_list = []
    for url in urls:
        self.download(None, None, None, [url], None, None, None, None, auto=False)
    return list(self.queue_list)
```

Place this method on `Download` immediately before `download_queue`. It may build queue items through the existing `download()` logic but must not call `download_queue()`.

- [ ] **Step 2: Add the intake command**

```python
@run.command(name="get")
@click.argument("input_value", nargs=-1, required=True)
@click.option("--dry-run", is_flag=True, help="Resolve and show the download plan without queueing")
@click.option("--json", "as_json", is_flag=True, help="Output a stable JSON plan")
@click.option("--yes", is_flag=True, help="Queue a non-empty resolved plan without prompting")
def get_command(input_value, dry_run, as_json, yes):
    """Resolve supported input and queue Deezer downloads."""
    from deemon.core.resolver import InputResolver, ResolutionStatus
    result = InputResolver().resolve(" ".join(input_value))
    plan = result.to_dict()
    if as_json:
        click.echo(json.dumps(plan, ensure_ascii=False))
    if result.status is not ResolutionStatus.RESOLVED:
        raise click.ClickException("Nothing was queued because resolution was not unique.")
    if dry_run:
        return
    if not yes:
        click.confirm(f"Queue {len(result.items)} item(s)?", abort=True)
    downloader = download.Download()
    downloader.queue_resolved_urls([item.deezer_url for item in result.items])
    downloader.download_queue()
```

- [ ] **Step 3: Verify no-download paths**

Run:

```bash
python3 -m deemon get --help
python3 -m deemon get --dry-run --json https://www.deezer.com/album/123
```

Expected: help lists `--dry-run`, `--json`, and `--yes`; dry-run returns a JSON plan and does not contact deemix.

- [ ] **Step 4: Compile changed modules**

Run: `python3 -m py_compile deemon/cli.py deemon/cmd/download.py deemon/core/resolver.py`

Expected: exit status `0`.

- [ ] **Step 5: Commit the safe intake workflow**

```bash
git add deemon/cli.py deemon/cmd/download.py deemon/core/resolver.py
git commit -m "feat: add universal download intake command"
```

### Task 6: Document the new automation surface

**Files:**
- Modify: `README.md:333-445`
- Modify: `docs/docs/commands/download.md:19-55`

- [ ] **Step 1: Add concise examples**

```markdown
## Universal intake

Resolve without downloading:

```bash
deemon resolve --json "https://open.spotify.com/album/..."
```

Preview a download without queueing:

```bash
deemon get --dry-run "Artist - Album"
```

Queue an already-reviewed plan from automation:

```bash
deemon get --yes "https://www.deezer.com/album/123"
```
```

Document that direct Deezer inputs work without Spotify configuration, that Spotify individual links use an optional resolver fallback, and that unconfigured Spotify playlists return an actionable capability error.

- [ ] **Step 2: Verify examples match installed command help**

Run:

```bash
python3 -m deemon resolve --help
python3 -m deemon get --help
```

Expected: every documented option appears in the corresponding help text.

- [ ] **Step 3: Check documentation formatting and compile all changed Python files**

Run:

```bash
git diff --check
python3 -m py_compile deemon/cli.py deemon/cmd/download.py deemon/core/resolver.py
```

Expected: both commands exit `0`.

- [ ] **Step 4: Commit documentation**

```bash
git add README.md docs/docs/commands/download.md
git commit -m "docs: explain universal download intake"
```

## Final manual QA gate

- [ ] In a terminal, run `python3 -m deemon` and verify the existing menu still appears unchanged.
- [ ] Run `python3 -m deemon get --dry-run "https://www.deezer.com/album/123"` and confirm no download progress, queue CSV write, or deemix login occurs.
- [ ] Run `python3 -m deemon resolve --json "https://open.spotify.com/playlist/example"` with no Spotify credentials and confirm the response is an explicit capability error rather than a traceback.
- [ ] Inspect `git status --short`; preserve unrelated `.superpowers/` artifacts and report them as untracked rather than staging them.

## Follow-on plans

1. Queue inspection/retry and `doctor` command.
2. TUI Download-Hub and status row that invoke the phase-1 intake API.
3. Raycast, Keyboard Maestro, and MCP migration to stable commands.
4. Remaining non-interactive parity for configuration/profile mutation, backup restore selection, and search candidate selection.
