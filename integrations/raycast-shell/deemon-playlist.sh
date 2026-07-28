#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Deemon • Playlist - URL
# @raycast.mode fullOutput
# @raycast.packageName Deemon
# Optional parameters:
# @raycast.icon https://raw.githubusercontent.com/deathrashed/deemon/main/deemon/assets/images/deemix.png
# @raycast.currentDirectoryPath ~
# @raycast.argument1 { "type": "text", "placeholder": "Playlist URL (Spotify/Deezer)" }
# Documentation:
# @raycast.description Download playlist by URL (checks existing collection)
# @raycast.author deathrashed
# @raycast.authorURL https://github.com/deathrashed

# Set HOME to your user directory (critical for deemix to find ARL)

# Set XDG_CONFIG_HOME to point to where deemix config actually is

# Add user's local bin to PATH (where pip installs tools)

# Change to deemon source directory

# Call deemon with -c flag (skip existing tracks)
deemon playlist -c "$1"

# Exit with deemon's exit code
exit $?
