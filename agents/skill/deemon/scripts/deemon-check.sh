#!/usr/bin/env bash
set -euo pipefail

DEEMON_DIR="${DEEMON_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
VENV_PYTHON="$DEEMON_DIR/.venv/bin/python"
DEEMON="$DEEMON_DIR/.venv/bin/deemon"

# Resolve config and db paths
if [ -f "$HOME/Library/Application Support/deemon/config.json" ]; then
  CONFIG_DIR="$HOME/Library/Application Support/deemon"
elif [ -f "$XDG_CONFIG_HOME/deemon/config.json" ]; then
  CONFIG_DIR="$XDG_CONFIG_HOME/deemon"
elif [ -f "$HOME/.config/deemon/config.json" ]; then
  CONFIG_DIR="$HOME/.config/deemon"
else
  echo "ERROR: Could not find deemon config directory"
  exit 1
fi

CONFIG="$CONFIG_DIR/config.json"
DB="$CONFIG_DIR/deemon.db"

echo "=== deemon Health Check ==="
echo ""

# 1. Venv
echo "--- Python ---"
if [ -x "$VENV_PYTHON" ]; then
  echo "  venv: OK ($VENV_PYTHON)"
else
  echo "  venv: MISSING"
fi
if [ -x "$DEEMON" ]; then
  echo "  CLI:  OK ($DEEMON)"
  echo "  ver:  $($DEEMON --version 2>/dev/null || echo 'unknown')"
else
  echo "  CLI:  MISSING"
fi

# 2. Config
echo ""
echo "--- Config ---"
if [ -f "$CONFIG" ]; then
  echo "  path: $CONFIG"
  ARL=$(python3 -c "import json; c=json.load(open('$CONFIG')); print('set' if c.get('deemix',{}).get('arl') else 'EMPTY')" 2>/dev/null || echo "parse error")
  echo "  ARL:  $ARL"
  BITRATE=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c.get('global',{}).get('bitrate','unknown'))" 2>/dev/null)
  echo "  bitrate: $BITRATE"
  PROFILES=$(python3 -c "
import json
c=json.load(open('$CONFIG'))
for k,v in c.items():
  if isinstance(v, dict) and k not in ('exclusions','new_releases','global','deemix','smtp_settings','plex'):
    print(f'  profile: {k}')
" 2>/dev/null || true)
else
  echo "  path: NOT FOUND at $CONFIG"
fi

# 3. Database
echo ""
echo "--- Database ---"
if [ -f "$DB" ]; then
  echo "  path: $DB"
  echo "  size: $(du -h "$DB" | cut -f1)"
  MONITORED=$(python3 -c "
import sqlite3
con = sqlite3.connect('$DB')
cur = con.cursor()
cur.execute('SELECT COUNT(*) FROM monitor WHERE profile_id=1')
count = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM releases WHERE profile_id=1')
releases = cur.fetchone()[0]
print(f'artists: {count}')
print(f'releases: {releases}')
con.close()
" 2>/dev/null || echo "  query error")
  echo "  $MONITORED"
else
  echo "  path: NOT FOUND"
fi

# 4. Deemix config
echo ""
echo "--- Deemix ---"
if [ -f "$HOME/.config/deemix/config.json" ]; then
  echo "  config: $HOME/.config/deemix/config.json"
elif [ -f "$HOME/Library/Application Support/deemix/config.json" ]; then
  echo "  config: $HOME/Library/Application Support/deemix/config.json"
else
  echo "  config: NOT FOUND"
fi

# 5. Filesystem
echo ""
echo "--- Downloads ---"
DOWNLOAD_PATH=$(python3 -c "
import json
c=json.load(open('$CONFIG'))
dp = c.get('global',{}).get('download_path','')
print(dp if dp else '(not set - using deemix default)')
" 2>/dev/null)
echo "  path: $DOWNLOAD_PATH"

echo ""
echo "=== Done ==="
