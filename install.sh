#!/usr/bin/env bash
set -e

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_PATH="$SRC_DIR/foxvc"

# Ensure foxvc runner is executable
chmod +x "$BIN_PATH"

echo "🦊 Installing FoxVC v0.5.2x..."

# Prefer user-local bin (~/.local/bin) to avoid sudo and avoid PEP 668 system conflicts
USER_BIN="$HOME/.local/bin"
mkdir -p "$USER_BIN"

ln -sf "$BIN_PATH" "$USER_BIN/foxvc"

# Ensure ~/.local/bin is in PATH for bash/zsh
SHELL_RC=""
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if [ -f "$SHELL_RC" ]; then
    if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$SHELL_RC"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    fi
fi

echo "=========================================================="
echo "✓ [SUCCESS] FoxVC installed to $USER_BIN/foxvc"
echo "✓ Instant check: run 'foxvc' or '~/.local/bin/foxvc'"
echo "=========================================================="
