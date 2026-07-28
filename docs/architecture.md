# Repository taxonomy

`deemon/` contains the installable application. `deemon/core/` owns configuration, database, API, and downloader integration; `deemon/cmd/` owns command behaviour; `deemon/plugins/` contains optional service adapters; and `deemon/utils/` contains shared presentation and input utilities.

`scripts/` holds portable development and automation utilities. `deemon/integrations/` holds the MCP server and Raycast bridge implementations, while `scripts/deemon-mcp.py` and `scripts/raycast-bridge.py` are their executable launchers. `integrations/keyboard-maestro/` and `integrations/raycast-shell/` hold optional external integration assets; `agents/` holds agent-facing guidance. `examples/` holds sanitized configuration references.

Runtime credentials belong in deemon's application config, not this repository:

- Deezer ARL: `deemix.arl`
- Spotify client ID: `spotify.client_id`
- Spotify client secret: `spotify.client_secret`

Manage them through `deemon settings set`, the interactive **Configuration → Connections & Health** screen, or `deemon doctor --json`. Existing deemix ARL and Spotify plugin settings are read only as one-time migration sources.

Deemix remains the owner of download templates, quality, queue, and output settings. Deemon continues to load the configured deemix directory through `deemix.settings.load`; it does not replace or remove either `~/.config/deemix/config.json` or `~/Library/Application Support/deemix/config.json`.
