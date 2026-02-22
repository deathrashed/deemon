#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Deemon - Download from File
# @raycast.mode fullOutput
# @raycast.packageName Deemon
# Optional parameters:
# @raycast.icon /Users/rd/deemon/deemon/assets/images/deemix-yellow.png
# @raycast.currentDirectoryPath ~
# @raycast.argument1 { "type": "text", "placeholder": "Path to file with album list" }
# Documentation:
# @raycast.description Download albums from file (one album/URL per line)
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
    echo "Usage: Provide path to a file containing album URLs or IDs"
    echo ""
    echo "File format: One album URL or ID per line"
    echo ""
    echo "Example file contents:"
    echo "  https://www.deezer.com/album/103248"
    echo "  123456789"
    echo "  https://www.deezer.com/album/987654"
    exit 1
fi

# Call deemon with album-file option
python3 -m deemon download --album-file "$1"

# Exit with deemon's exit code
exit $?
