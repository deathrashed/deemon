#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Deemon - Monitor Artist
# @raycast.mode fullOutput
# @raycast.packageName Deemon
# Optional parameters:
# @raycast.icon ./deemon/assets/images/deemix-green.png
# @raycast.currentDirectoryPath ~
# @raycast.argument1 { "type": "text", "placeholder": "Artist Name" }
# Documentation:
# @raycast.description Monitor artist for new releases
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
    echo "Usage: Provide an artist name to monitor"
    echo ""
    echo "Example: Metallica"
    exit 1
fi

# Call deemon
python3 -m deemon monitor "$1"

# Exit with deemon's exit code
exit $?
