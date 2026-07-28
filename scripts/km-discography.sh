#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ "$(uname -s)" == "Darwin" ]]; then
    CONSOLE_USER="$(stat -f '%Su' /dev/console 2>/dev/null || true)"
    if [[ -n "$CONSOLE_USER" && "$CONSOLE_USER" != "root" && "$CONSOLE_USER" != "loginwindow" ]]; then
        CONSOLE_HOME="$(dscl . -read "/Users/$CONSOLE_USER" NFSHomeDirectory 2>/dev/null | awk '{print $2}')"
        if [[ -n "$CONSOLE_HOME" && -d "$CONSOLE_HOME" ]]; then
            export HOME="$CONSOLE_HOME"
            export XDG_CONFIG_HOME="$CONSOLE_HOME/.config"
        fi
    fi
fi

exec "$PROJECT_ROOT/.venv/bin/python" -m deemon.integrations.km "$@"
