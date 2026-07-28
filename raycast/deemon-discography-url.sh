#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Deemon • Discography - Spotify URL
# @raycast.mode fullOutput
# @raycast.packageName Deemon
# Optional parameters:
# @raycast.icon ~/Scripts/Riley/audio/download/deemon/deemon/assets/images/deemix-green.png
# @raycast.currentDirectoryPath ~
# @raycast.argument1 { "type": "text", "placeholder": "Spotify Album URL" }
# Documentation:
# @raycast.description Download full artist discography from a Spotify or Deezer album link
# @raycast.author deathrashed
# @raycast.authorURL https://github.com/deathrashed

# Set HOME to your user directory (critical for deemix to find ARL)
export HOME="/Users/rd"

# Set XDG_CONFIG_HOME to point to where deemix config actually is
export XDG_CONFIG_HOME="/Users/rd/.config"

# Add user's local bin to PATH (where pip installs tools)
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

# Change to deemon source directory
cd "$HOME/Scripts/Riley/audio/download/deemon" 2>/dev/null || true

if [ -z "$1" ]; then
    echo "Usage: Provide a Spotify or Deezer album URL"
    echo ""
    echo "Example:"
    echo "  https://open.spotify.com/album/..."
    echo "  https://www.deezer.com/album/..."
    echo ""
    echo "This will resolve the album's main artist and download their full discography."
    exit 1
fi

python3 -m deemon discography --url "$1" --include-singles

# Exit with deemon's exit code
exit $?
