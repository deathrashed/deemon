# Scripts

Project-owned utility entry points live here.

- `install.sh`: creates `.venv` and installs this checkout in editable mode.
- `uninstall.sh`: removes deemon from this checkout's virtual environment without touching user configuration.
- `deemon-wrapper.sh`: starts the CLI using the checkout virtual environment when present. On macOS it resolves the active console user's `HOME` and XDG configuration paths, so GUI automation tools use the same deemon and Deemix settings as Terminal.
- `deemon-debug.sh`: prints non-sensitive environment and health information, then starts the CLI.
- `deemon_download_missing.py`: compares a Deezer discography with the configured collection and downloads only missing releases.
- `deemon-mcp.py`: starts the MCP server implementation in `deemon/integrations/mcp.py`.
- `raycast-bridge.py`: starts the JSON bridge implementation in `deemon/integrations/raycast.py`.
- `km-discography.sh`: runs the Keyboard Maestro-friendly discography command from this checkout and returns a clean plain-text report.
- `km-get.sh`: resolves a URL or search query for Keyboard Maestro, with read-only preview and clean download-report modes.

The root `install.sh` and `uninstall.sh` are short convenience launchers for the two installation scripts above.
