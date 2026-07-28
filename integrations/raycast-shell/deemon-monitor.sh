#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Deemon • Monitor - Add Artist
# @raycast.mode fullOutput
# @raycast.packageName Deemon
# Optional parameters:
# @raycast.icon https://raw.githubusercontent.com/deathrashed/deemon/main/deemon/assets/images/deemix-aqua.png
# @raycast.currentDirectoryPath ~
# @raycast.argument1 { "type": "text", "placeholder": "Artist Name" }
# Documentation:
# @raycast.description Monitor artist for new releases
# @raycast.author deathrashed
# @raycast.authorURL https://github.com/deathrashed

# Set HOME to your user directory (critical for deemix to find ARL)

# Set XDG_CONFIG_HOME to point to where deemix config actually is

# Add user's local bin to PATH (where pip installs tools)

# Change to deemon source directory

# If no argument provided, show help
if [ -z "$1" ]; then
    echo "Usage: Provide an artist name to monitor"
    echo ""
    echo "Example: Metallica"
    exit 1
fi

# Call deemon
deemon monitor "$1"

# Exit with deemon's exit code
exit $?
