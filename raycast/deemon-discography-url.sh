#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Deemon - Discography from Spotify Album
# @raycast.mode fullOutput
# @raycast.packageName Deemon
# Optional parameters:
# @raycast.icon /Users/rd/deemon/deemon/assets/images/deemix-green.png
# @raycast.currentDirectoryPath ~
# @raycast.argument1 { "type": "text", "placeholder": "Spotify Album URL" }
# Documentation:
# @raycast.description Download full artist discography from a Spotify album link
# @raycast.author deathrashed
# @raycast.authorURL https://github.com/deathrashed

# Set HOME to your user directory (critical for deemix to find ARL)
export HOME="/Users/rd"

# Set XDG_CONFIG_HOME to point to where deemix config actually is
export XDG_CONFIG_HOME="/Users/rd/.config"

# Add user's local bin to PATH (where pip installs tools)
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

# Change to deemon source directory
cd "/Users/rd/deemon" 2>/dev/null || true

if [ -z "$1" ]; then
    echo "Usage: Provide a Spotify album URL"
    echo ""
    echo "Example:"
    echo "  https://open.spotify.com/album/..."
    echo ""
    echo "This will resolve the album's main artist and download their full discography."
    exit 1
fi

ARTIST_AND_ALBUM="$(
python3 - "$1" <<'PY'
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
    request = Request(url, headers=headers or {}, data=data)
    with urlopen(request, timeout=10) as response:
        return json.load(response)


spotify_url = sys.argv[1].strip()
album_match = re.search(r"spotify\.com/album/([A-Za-z0-9]+)", spotify_url)
if not album_match:
    fail("Error: Input must be a Spotify album URL.")

spotify_config = Path("/Users/rd/.config/deemix/spotify/config.json")
if not spotify_config.exists():
    fail(f"Error: Spotify config not found at {spotify_config}")

try:
    config = json.loads(spotify_config.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    fail(f"Error: Could not parse Spotify config: {exc}")

client_id = (config.get("clientId") or "").strip()
client_secret = (config.get("clientSecret") or "").strip()
if not client_id or not client_secret:
    fail("Error: Spotify credentials are missing from deemix config.")

credentials = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")

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
        fail("Error: Spotify token response did not include an access token.")

    album_id = album_match.group(1)
    album_data = fetch_json(
        f"https://api.spotify.com/v1/albums/{album_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
except HTTPError as exc:
    fail(f"Error: Spotify API request failed with HTTP {exc.code}.")
except URLError as exc:
    fail(f"Error: Could not reach Spotify API: {exc.reason}")
except Exception as exc:
    fail(f"Error: Failed to resolve Spotify album: {exc}")

artists = album_data.get("artists") or []
album_name = (album_data.get("name") or "").strip()
artist_name = ((artists[0] or {}).get("name") or "").strip() if artists else ""

if not artist_name or not album_name:
    fail("Error: Spotify album response did not include artist and album names.")

print(f"{artist_name}|{album_name}")
PY
)"
status=$?

if [ $status -ne 0 ]; then
    exit $status
fi

artist_name="${ARTIST_AND_ALBUM%%|*}"
album_name="${ARTIST_AND_ALBUM#*|}"

echo "Resolved artist: $artist_name"
echo "Resolved album: $album_name"
echo ""

python3 -m deemon discography -b "$artist_name" -a "$album_name" --include-singles

# Exit with deemon's exit code
exit $?
