#!/usr/bin/env bash

echo "=== DEBUG INFO ==="
echo "HOME: $HOME"
echo "USER: $USER"
echo "PATH: $PATH"
echo "Current dir: $(pwd)"
echo "Python: $(which python3)"
echo "Python version: $(python3 --version)"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
    PYTHON="$PROJECT_ROOT/.venv/bin/python"
else
    PYTHON="${PYTHON:-python3}"
fi

cd "$PROJECT_ROOT"

echo "After setting:"
echo "HOME: $HOME"
echo "Current dir: $(pwd)"
echo ""

"$PYTHON" -m deemon doctor --json
echo ""

exec "$PYTHON" -m deemon "$@"
