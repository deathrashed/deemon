#!/usr/bin/env bash
# Usage: deemon-query.sh <sql_query>
# Runs a read-only SQL query against the deemon database.

set -euo pipefail

if [ $# -eq 0 ]; then
  echo "Usage: deemon-query.sh <sql_query>"
  echo ""
  echo "Examples:"
  echo "  deemon-query.sh 'SELECT * FROM monitor'"
  echo "  deemon-query.sh 'SELECT artist_name, album_name FROM releases WHERE future_release=1'"
  echo "  deemon-query.sh 'SELECT COUNT(*) FROM releases'"
  exit 1
fi

# Find the database
for DIR in "$HOME/Library/Application Support/deemon" "$XDG_CONFIG_HOME/deemon" "$HOME/.config/deemon"; do
  if [ -f "$DIR/deemon.db" ]; then
    DB="$DIR/deemon.db"
    break
  fi
done

if [ -z "${DB:-}" ]; then
  echo "ERROR: deemon.db not found" >&2
  exit 1
fi

python3 -c "
import sqlite3, sys
try:
    con = sqlite3.connect('$DB')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sys.argv[1])
    rows = cur.fetchall()
    if rows:
        headers = rows[0].keys()
        print(' | '.join(headers))
        print('-' * len(' | '.join(headers)))
        for row in rows:
            print(' | '.join(str(row[h] or '') for h in headers))
    else:
        print('(no results)')
    con.close()
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" "$@"
