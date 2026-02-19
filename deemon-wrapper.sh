#!/usr/bin/env bash
#
# deemon wrapper script for Keyboard Maestro
# This script ensures the correct environment for deemon
#

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set HOME to your user directory (critical for deemix to find ARL)
export HOME="/Users/rd"

# Set XDG_CONFIG_HOME to point to where deemix config actually is
export XDG_CONFIG_HOME="/Users/rd/.config"

# Add user's local bin to PATH (where pip installs tools)
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

# Change to deemon source directory (editable install) - uses script location
cd "$SCRIPT_DIR" 2>/dev/null || true

# Call deemon with all arguments passed to this script
python3 -m deemon "$@"

# Exit with deemon's exit code
exit $?
