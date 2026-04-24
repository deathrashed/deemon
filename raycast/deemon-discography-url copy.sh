#!/usr/bin/env bash
set -euo pipefail

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Deemon - Discography from Spotify URL
# @raycast.mode fullOutput
# @raycast.packageName Deemon
# Optional parameters:
# @raycast.icon /Users/rd/deemon/deemon/assets/images/deemix-yellow.png
# @raycast.currentDirectoryPath ~
# @raycast.argument1 { "type": "text", "placeholder": "Spotify Album URL" }
# Documentation:
# @raycast.description Download the input Spotify album, then the artist discography
# @raycast.author deathrashed
# @raycast.authorURL https://github.com/deathrashed

# Environment so deemix/deemon can find config + ARL
export HOME="/Users/rd"
export XDG_CONFIG_HOME="/Users/rd/.config"
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

DEEMON_DIR="/Users/rd/deemon"
SPOTIFY_CONFIG="/Users/rd/.config/deemix/spotify/config.json"
SPOTIFY_URL="${1:-}"

# Change to deemon source directory
cd "$DEEMON_DIR" 2>/dev/null || true

fail() {
  echo "Error: $*" >&2
  exit 1
}

if [[ -z "$SPOTIFY_URL" ]]; then
  cat <<'EOF'
Usage: Provide a Spotify album URL

Example:
  https://open.spotify.com/album/...

This will:
1. Download the provided album URL explicitly
2. Resolve the album's main artist
3. Download the rest of that artist's discography
EOF
  exit 1
fi

ARTIST_AND_ALBUM="$(
python3 - "$SPOTIFY_URL" "$SPOTIFY_CONFIG" <<'PY'
import base64
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def fetch_json(url: str, headers=None, data=None):
    req = Request(url, headers=headers or {}, data=data)
    with urlopen(req, timeout=15) as resp:
        return json.load(resp)


spotify_url = sys.argv[1].strip()
spotify_config = Path(sys.argv[2])

album_match = re.search(r"spotify\.com/album/([A-Za-z0-9]+)", spotify_url)
if not album_match:
    fail("Input must be a Spotify album URL.")

if not spotify_config.exists():
    fail(f"Spotify config not found at {spotify_config}")

try:
    config = json.loads(spotify_config.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    fail(f"Could not parse Spotify config: {exc}")

client_id = (config.get("clientId") or "").strip()
client_secret = (config.get("clientSecret") or "").strip()
if not client_id or not client_secret:
    fail("Spotify credentials are missing from deemix config.")

credentials = base64.b64encode(
    f"{client_id}:{client_secret}".encode("utf-8")
).decode("utf-8")

try:
    token_data = fetch_json(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=urlencode({"grant_type": "client_credentials"}).encode("utf-8"),
    )
    access_token = token_data.get("access_token")
    if not access_token:
        fail("Spotify token response did not include an access token.")

    album_id = album_match.group(1)
    album_data = fetch_json(
        f"https://api.spotify.com/v1/albums/{album_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
except HTTPError as exc:
    fail(f"Spotify API request failed with HTTP {exc.code}.")
except URLError as exc:
    fail(f"Could not reach Spotify API: {exc.reason}")
except Exception as exc:
    fail(f"Failed to resolve Spotify album: {exc}")

artists = album_data.get("artists") or []
album_name = (album_data.get("name") or "").strip()
artist_name = ((artists[0] or {}).get("name") or "").strip() if artists else ""

if not artist_name or not album_name:
    fail("Spotify album response did not include artist and album names.")

print(f"{artist_name}|{album_name}")
PY
)"

artist_name="${ARTIST_AND_ALBUM%%|*}"
album_name="${ARTIST_AND_ALBUM#*|}"

echo "Resolved artist: $artist_name"
echo "Resolved album: $album_name"
echo ""

echo "Step 1/2: Downloading the input album URL explicitly..."
python3 -m deemon download -u "$SPOTIFY_URL"

echo ""
echo "Step 2/2: Downloading remaining discography..."
# Albums + EPs only. Remove/change flags here if your deemon fork uses different filtering.
python3 -m deemon discography -b "$artist_name" -a "$album_name"

exit $?