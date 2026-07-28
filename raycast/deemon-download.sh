#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Deemon • Band - Album
# @raycast.mode fullOutput
# @raycast.packageName Deemon
# Optional parameters:
# @raycast.icon ~/Scripts/Riley/audio/download/deemon/deemon/assets/images/deemix-pink.png
# @raycast.currentDirectoryPath ~
# @raycast.argument1 { "type": "text", "placeholder": "Artist Name" }
# @raycast.argument2 { "type": "text", "placeholder": "Album Name" }
# Documentation:
# @raycast.description Download album by artist and album name
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

# Call deemon directly
python3 -m deemon get --yes "$1 - $2"

# Exit with deemon's exit code
exit $?
