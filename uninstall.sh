#!/usr/bin/env bash
#
# deemon uninstallation script
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo ""
echo "=================================="
echo "  deemon Uninstall Script"
echo "=================================="
echo ""

# Find pip command
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    echo "Error: pip not found"
    exit 1
fi

# Check if deemon is installed
if ! $PIP_CMD show deemon &> /dev/null; then
    warn "deemon is not installed"
    exit 0
fi

warn "This will uninstall deemon."
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    info "Uninstall cancelled"
    exit 0
fi

info "Uninstalling deemon..."
$PIP_CMD uninstall -y deemon

info "deemon has been uninstalled"
echo ""
info "Note: Your configuration and database are preserved at:"
info "  ~/.config/deemon/"
info "  ~/.local/share/deemon/"
echo ""
