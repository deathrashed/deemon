#!/usr/bin/env bash
#
# deemon installation script
# Installs deemon globally so you can run it with just 'deemon' command
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print functions
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Check Python version
check_python() {
    info "Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed. Please install Python 3.8 or higher."
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

    info "Found Python $PYTHON_VERSION"

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        error "Python 3.8 or higher is required. You have Python $PYTHON_VERSION"
    fi

    if [ "$PYTHON_MINOR" -ge 8 ]; then
        info "Python version check passed!"
    fi
}

# Check if pip is available
check_pip() {
    info "Checking for pip..."

    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        error "pip is not installed. Please install pip first."
    fi

    # Use pip3 if available, otherwise fall back to pip
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    else
        PIP_CMD="pip"
    fi

    info "Using $PIP_CMD"
}

# Check if deemon is already installed
check_existing() {
    if $PIP_CMD show deemon &> /dev/null; then
        warn "deemon is already installed."
        read -p "Do you want to reinstall? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            info "Uninstalling existing deemon..."
            $PIP_CMD uninstall -y deemon
        else
            info "Installation cancelled."
            exit 0
        fi
    fi
}

# Install deemon
install_deemon() {
    info "Installing deemon in editable mode..."
    info "This means changes to the source code will take effect immediately!"
    $PIP_CMD install --user -e "$SCRIPT_DIR" || error "Installation failed"
    info "Installation completed successfully!"
}

# Fix the entry point script if needed
fix_entrypoint() {
    info "Verifying installation..."

    # Get the current user's home directory
    HOME_DIR="$HOME"
    if [ -z "$HOME_DIR" ]; then
        HOME_DIR="$(eval echo ~$USER)"
    fi

    # Find the installed script location
    DEEMON_SCRIPT=$($PIP_CMD show deemon 2>/dev/null | grep "Location:" | cut -d' ' -f2)/../bin/deemon 2>/dev/null
    if [ -z "$DEEMON_SCRIPT" ] || [ ! -f "$DEEMON_SCRIPT" ]; then
        DEEMON_SCRIPT="$HOME_DIR/.local/bin/deemon"
    fi

    # Get the directory where install.sh is located (deemon source)
    SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [ -f "$DEEMON_SCRIPT" ]; then
        info "Updating entry point script at: $DEEMON_SCRIPT"
        cat > "$DEEMON_SCRIPT" << EOF
#!/bin/bash
# Set HOME explicitly (needed for Keyboard Maestro and other tools)
export HOME="\${HOME:-$HOME_DIR}"
export USER="\${USER:-$(whoami)}"

# Set PATH to find python3
export PATH="\$HOME/.local/bin:/usr/local/bin:\$PATH"

# Change to deemon source directory (editable install)
cd "$SOURCE_DIR" 2>/dev/null || true

# Run deemon
exec python3 -m deemon "\$@"
EOF
        chmod +x "$DEEMON_SCRIPT"
        info "Entry point script updated!"
    else
        warn "Could not find deemon script at $DEEMON_SCRIPT"
    fi
}

# Verify installation
verify_install() {
    info "Verifying installation..."

    # Test if deemon command works
    if command -v deemon &> /dev/null; then
        if deemon --help &> /dev/null; then
            info "deemon is installed and working!"
            echo ""
            info "Quick commands:"
            echo "  deemon cheatsheet    Show command reference"
            echo "  deemon               Interactive menu"
            echo "  deemon --help        Show all commands"
        else
            warn "deemon command found but may not work correctly."
            warn "Try running: python3 -m deemon --help"
        fi
    else
        warn "deemon command not found in PATH."
        warn "The package is installed, but you may need to add this to your PATH:"
        warn "  $(python3 -m site --user-base)/bin"
        info "You can still run deemon with: python3 -m deemon"
    fi
}

# Main installation
main() {
    echo ""
    echo "=================================="
    echo "  deemon Installation Script"
    echo "=================================="
    echo ""

    # Get script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    check_python
    check_pip
    check_existing
    install_deemon
    fix_entrypoint
    verify_install

    echo ""
    info "Installation complete!"
    echo ""
    info "Quick start:"
    echo "  deemon cheatsheet    Show all commands"
    echo "  deemon               Interactive menu"
    echo "  deemon --init        Initialize database"
    echo ""
    info "Set your ARL token (required for downloads):"
    echo "  deemon --arl YOUR_TOKEN_HERE"
    echo ""
    info "Monitor your first artist:"
    echo "  deemon monitor \"Artist Name\""
    echo ""
    info "For more help: deemon --help or deemon cheatsheet"
    echo ""
}

# Run main
main
