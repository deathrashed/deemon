#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Deemon • Band - Album
# @raycast.mode fullOutput
# @raycast.packageName Deemon
# Optional parameters:
# @raycast.icon https://raw.githubusercontent.com/deathrashed/deemon/main/deemon/assets/images/deemix-pink.png
# @raycast.currentDirectoryPath ~
# @raycast.argument1 { "type": "text", "placeholder": "Artist Name" }
# @raycast.argument2 { "type": "text", "placeholder": "Album Name" }
# Documentation:
# @raycast.description Download album by artist and album name
# @raycast.author deathrashed
# @raycast.authorURL https://github.com/deathrashed

# Set HOME to your user directory (critical for deemix to find ARL)

# Set XDG_CONFIG_HOME to point to where deemix config actually is

# Add user's local bin to PATH (where pip installs tools)

# Change to deemon source directory

# Call deemon directly
deemon get --yes "$1 - $2"

# Exit with deemon's exit code
exit $?
