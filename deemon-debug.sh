#!/usr/bin/env bash
#
# Debug wrapper to see what's happening
#

echo "=== DEBUG INFO ==="
echo "HOME: $HOME"
echo "USER: $USER"
echo "PATH: $PATH"
echo "Current dir: $(pwd)"
echo "Python: $(which python3)"
echo "Python version: $(python3 --version)"
echo ""

# Check if config exists
if [ -f "$HOME/.local/share/deemon/config.json" ]; then
    echo "Config file EXISTS at: $HOME/.local/share/deemon/config.json"
    echo "ARL in config: $(grep -o '"arl"[[:space:]]*:[[:space:]]*"[^"]*"' "$HOME/.local/share/deemon/config.json" | cut -d'"' -f4 | head -c 10)..."
else
    echo "Config file NOT FOUND at: $HOME/.local/share/deemon/config.json"
fi
echo ""

# Set environment
export HOME="/Users/rd"
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
cd /Users/rd/deemon

echo "After setting:"
echo "HOME: $HOME"
echo "Current dir: $(pwd)"
echo ""

# Run deemon
python3 -m deemon "$@"
