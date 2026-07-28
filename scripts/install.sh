#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
VENV="$PROJECT_ROOT/.venv"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python 3.8 or newer is required." >&2
    exit 1
fi

if ! "$PYTHON" -c 'import sys; raise SystemExit(sys.version_info < (3, 8))'; then
    echo "Python 3.8 or newer is required." >&2
    exit 1
fi

if [[ ! -x "$VENV/bin/python" ]]; then
    "$PYTHON" -m venv "$VENV"
fi

if ! "$VENV/bin/python" -m pip --version >/dev/null 2>&1; then
    "$VENV/bin/python" -m ensurepip --upgrade
fi

PIP_USER=false "$VENV/bin/python" -m pip install --upgrade pip
PIP_USER=false "$VENV/bin/python" -m pip install --editable "$PROJECT_ROOT"
"$VENV/bin/python" -m deemon --help >/dev/null

cat <<EOF

deemon is installed in this checkout.

  $VENV/bin/deemon --init
  $VENV/bin/deemon

To make the command available in every shell, install this repository with pipx:

  pipx install --editable "$PROJECT_ROOT"
EOF
