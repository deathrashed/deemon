#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Deemon - Refresh
# @raycast.mode fullOutput
# @raycast.packageName Deemon
# Optional parameters:
# @raycast.icon ./deemon/assets/images/deemix-orange.png
# @raycast.currentDirectoryPath ~
# Documentation:
# @raycast.description Check monitored artists for new releases
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

# Call deemon
python3 -m deemon refresh

# Exit with deemon's exit code
exit $?
