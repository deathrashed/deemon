# deemon Module Guide (Music Monitoring & Downloader)

**deemon** is a Python-based CLI tool designed to monitor music artists for new releases and automatically trigger downloads via `deemix`. It serves as a bridge between Deezer's metadata and local music libraries.

## 1. Deep Structural Analysis

The project is structured as a standalone Python package with supporting integration for macOS launchers.

### Core Architecture
- **Package Root (`deemon/`)**: Contains the core Python implementation.
  - `cli.py`: Click-based command definitions and interactive menu.
  - `core/`: Low-level API wrappers (`api.py`), database logic (`db.py`), and config management (`config.py`).
  - `cmd/`: Business logic for individual commands (monitor, refresh, download).
  - `utils/`: Common utilities for UI, validation, and date parsing.
- **Data Persistence**:
  - Config: `~/.config/deemon/config.json`
  - Database: `~/.local/share/deemon/deemon.db` (SQLite)
- **Scripts (`scripts/`)**: Portable shell and Python utilities for installation, diagnostics, automation wrappers, and one-off collection operations.
- **Integrations (`integrations/`)**: Optional Keyboard Maestro assets and Raycast shell integrations.
- **Package integrations (`deemon/integrations/`)**: MCP and Raycast bridge implementations.

## 2. Setup Documentation

### Prerequisites
- Python 3.10+
- `deemix` (python package)
- `deezer-python` (python package)
- `PlexAPI` (optional, for library refresh)

### Initial Installation
Execute these commands within the `deemon` directory:
```bash
./install.sh
```

### Configuration
1. Initialize the configuration and database:
   ```bash
   deemon --init
   ```
2. Edit `~/.config/deemon/config.json` and add your **ARL token** for Deezer authentication.

## 3. Navigation Guide

### Directory Map
- `deemon/core/`: The "Engine". Start here to understand API or DB changes.
- `deemon/cmd/`: The "Brain". Start here to add or modify command logic.
- `scripts/`: Portable utility entry points. `install.sh` and `uninstall.sh` at the repository root delegate here for convenience.
- `integrations/`: Optional external integration assets.
- `examples/`: Sanitized configuration examples; runtime settings do not belong in the repository.

### Quick Reference: "Where do I find X?"
- **Adding a new CLI command?** -> `deemon/cli.py` and a new file in `deemon/cmd/`.
- **Modifying the SQLite schema?** -> `deemon/core/db.py`.
- **Updating a Raycast integration?** -> `integrations/raycast-shell/` or the separately installed Raycast extension.

## 4. Code Patterns & Conventions

### CLI Architecture
- **Click**: All commands are defined using the `click` library in `cli.py`.
- **Interactive Menus**: Use the `ui.py` utilities for consistent terminal formatting.

### Data Patterns
- **Transactions**: The database tracks transactions to support the `rollback` command.
- **Profiles**: Supports multiple configuration profiles (e.g., "Main", "Test").

### Communication Pattern
- **Raycast Bridge**: `deemon/integrations/raycast.py` serves as a JSON-only interface for the Raycast extension. `scripts/raycast-bridge.py` is its executable launcher.

## 5. Extension Guidelines

### Adding a New Platform (e.g., Spotify, Bandcamp)
1. Add an API wrapper in `deemon/core/api.py`.
2. Update `deemon/cmd/monitor.py` to handle the new platform's artist/playlist lookup.
3. Add any necessary credentials to `core/config.py`.

### Modifying the Database
- Increment the version in `core/db.py`.
- Add a migration step in the `Database.migrate()` method.

## 6. Verification & Quality Assurance

### Verification Commands
- **Linting**: `python3 -m py_compile deemon/*.py`
- **Functional Test**: `deemon refresh --dry-run` to check for new releases without triggering downloads.
- **Email Test**: `deemon test -e` to verify SMTP settings.

### Common Pitfalls
- **ARL Expiration**: Downloads will fail silently or with "Not Logged In" if the ARL expires.
- **Fast API Threads**: High thread counts in `config.json` can lead to rate-limiting by Deezer.
