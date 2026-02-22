#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Deemon - Download Discography
# @raycast.mode fullOutput
# @raycast.packageName Deemon
# Optional parameters:
# @raycast.icon /Users/rd/deemon/deemon/assets/images/deemix-red.png
# @raycast.currentDirectoryPath ~
# @raycast.argument1 { "type": "text", "placeholder": "Artist Name" }
# @raycast.argument2 { "type": "text", "placeholder": "Album Name (to identify artist)" }
# Documentation:
# @raycast.description Download full artist discography
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

# If no arguments provided, prompt user
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: Provide artist name and an album name to identify the artist"
    echo ""
    echo "Example:"
    echo "  Artist: Pink Floyd"
    echo "  Album: The Dark Side of the Moon"
    echo ""
    echo "This will download Pink Floyd's full discography."
    exit 1
fi

# Call deemon with discography command including singles
python3 -m deemon discography -b "$1" -a "$2" --include-singles

# Exit with deemon's exit code
exit $?
