#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Deemon • Monitor - Show Releases
# @raycast.mode fullOutput
# @raycast.packageName Deemon
# Optional parameters:
# @raycast.icon https://raw.githubusercontent.com/deathrashed/deemon/main/deemon/assets/images/deemix-brown.png
# @raycast.currentDirectoryPath ~
# Documentation:
# @raycast.description Show recent releases from monitored artists
# @raycast.author deathrashed
# @raycast.authorURL https://github.com/deathrashed

# Set HOME to your user directory (critical for deemix to find ARL)

# Set XDG_CONFIG_HOME to point to where deemix config actually is

# Add user's local bin to PATH (where pip installs tools)

# Change to deemon source directory

# Call deemon
deemon show releases

# Exit with deemon's exit code
exit $?
