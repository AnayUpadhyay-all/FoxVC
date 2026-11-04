#!/usr/bin/env bash
# ============================================================================
# FoxVC Universal Zero-Config Installer (Android, Linux, macOS)
# Works both inside a cloned repository and via single-line curl pipe:
#   curl -sSL https://raw.githubusercontent.com/AnayUpadhyay-all/FoxVC/main/install.sh | bash
# ============================================================================
set -e

echo "=========================================================="
echo "          🦊 FoxVC Universal Installer"
echo "=========================================================="

REPO_URL="https://github.com/AnayUpadhyay-all/FoxVC.git"
INSTALL_ROOT=""

# 1. Determine Source Directory (Repo check or Auto-Clone)
SCRIPT_DIR=""
if [ -n "${BASH_SOURCE[0]}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/foxvc" ]; then
    INSTALL_ROOT="$SCRIPT_DIR"
    echo "✓ Using local FoxVC repository at $INSTALL_ROOT"
else
    # Running via curl | bash without prior clone
    TARGET_DIR="$HOME/.foxvc"
    echo "📦 Cloning FoxVC to $TARGET_DIR..."
    if command -v git >/dev/null 2>&1; then
        if [ -d "$TARGET_DIR/.git" ]; then
            git -C "$TARGET_DIR" pull --ff-only || true
        else
            rm -rf "$TARGET_DIR"
            git clone --depth 1 "$REPO_URL" "$TARGET_DIR"
        fi
        INSTALL_ROOT="$TARGET_DIR"
    else
        echo "❌ Error: 'git' is not installed. Please install git first (e.g., 'pkg install git' or 'apt install git')."
        exit 1
    fi
fi

BIN_PATH="$INSTALL_ROOT/foxvc"
chmod +x "$BIN_PATH"

# 2. Determine System Binary Target Directory
TARGET_BIN=""
if [ -n "$TERMUX_VERSION" ] || [ -d "/data/data/com.termux" ]; then
    # Android Termux Environment (default system PATH)
    TARGET_BIN="${PREFIX:-/data/data/com.termux/files/usr}/bin"
    echo "📱 Detected Android (Termux): target is $TARGET_BIN"
elif [ -w "/usr/local/bin" ]; then
    # Standard Unix with write permissions to /usr/local/bin
    TARGET_BIN="/usr/local/bin"
    echo "💻 Detected Unix system: target is $TARGET_BIN"
else
    # Fallback to user-local directory
    TARGET_BIN="$HOME/.local/bin"
    echo "💻 Detected Unix system: target is $TARGET_BIN"
fi

mkdir -p "$TARGET_BIN"
ln -sf "$BIN_PATH" "$TARGET_BIN/foxvc"
chmod +x "$TARGET_BIN/foxvc"

# 3. Compile Native C VM Engine for Device CPU Architecture (ARM64 / x86_64)
echo "⚙️ Building native C engine for local CPU..."
COMPILER=""
if command -v clang >/dev/null 2>&1; then
    COMPILER="clang"
elif command -v gcc >/dev/null 2>&1; then
    COMPILER="gcc"
fi

if [ -n "$COMPILER" ]; then
    $COMPILER -O3 -shared -fPIC "$INSTALL_ROOT/engine/foxvm.c" -o "$INSTALL_ROOT/engine/foxvm.so" -lm 2>/dev/null || true
    if [ -f "$INSTALL_ROOT/engine/foxvm.so" ]; then
        echo "✓ Native C engine compiled successfully."
    fi
fi

# 4. PATH Configuration (if not already present)
if ! echo "$PATH" | tr ":" "\n" | grep -qx "$TARGET_BIN"; then
    for RC in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        if [ -f "$RC" ]; then
            if ! grep -q "$TARGET_BIN" "$RC"; then
                echo "export PATH=\"$TARGET_BIN:\$PATH\"" >> "$RC"
            fi
        fi
    done
fi

echo "=========================================================="
echo "🎉 FoxVC is ready to use!"
echo "=========================================================="
echo "👉 Simply type:  foxvc"
echo ""
echo "Quick Commands:"
echo "  foxvc run <file.fox>    - Run code"
echo "  foxvc build <file.fox>  - Compile to standalone native binary"
echo "  foxvc mobile            - Open mobile studio in your phone browser"
echo "=========================================================="
