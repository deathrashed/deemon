#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$PROJECT_ROOT/.venv"

if [[ ! -x "$VENV/bin/python" ]]; then
    echo "No project virtual environment exists at $VENV."
    exit 0
fi

read -r -p "Uninstall deemon from this project's virtual environment? [y/N] " reply
if [[ ! "$reply" =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

"$VENV/bin/python" -m pip uninstall --yes deemon
echo "deemon was removed from $VENV. Configuration and Deemix data were preserved."
