#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Deemon - Download by URL
# @raycast.mode fullOutput
# @raycast.packageName Deemon
# Optional parameters:
# @raycast.icon /Users/rd/deemon/deemon/assets/images/deemix-cyan.png
# @raycast.currentDirectoryPath ~
# @raycast.argument1 { "type": "text", "placeholder": "Deezer/Spotify URL (album/track/playlist/artist)", "optional": true }
# Documentation:
# @raycast.description Quick download by any Deezer or Spotify URL
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

# If no argument provided, show help
if [ -z "$1" ]; then
    echo "Usage: Provide a Deezer or Spotify URL"
    echo ""
    echo "Examples:"
    echo "  https://www.deezer.com/album/103248"
    echo "  https://www.deezer.com/track/3135556"
    echo "  https://www.deezer.com/playlist/908622995"
    echo "  https://www.deezer.com/artist/27"
    echo "  https://open.spotify.com/album/..."
    exit 1
fi

# Call deemon with global command
python3 -m deemon global "$1"

# Exit with deemon's exit code
exit $?
