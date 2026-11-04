#!/usr/bin/env bash
# ============================================================================
# FoxVC Official Android (Termux) Local Installer
# Sets up Python, Clang, compiles native ARM64 engine, and installs the CLI.
# ============================================================================
set -e

echo "============================================================"
echo "      🦊 FoxVC Local Android (Termux) Installer"
echo "============================================================"

# Verify running on Android / Termux
IS_TERMUX=false
if [ -n "$TERMUX_VERSION" ] || [ -d "/data/data/com.termux" ]; then
    IS_TERMUX=true
    echo "✓ Detected Android Termux environment."
else
    echo "ℹ Non-Termux Linux environment detected (running in compatibility mode)."
fi

# 1. Update packages and install dependencies
if [ "$IS_TERMUX" = true ] && command -v pkg >/dev/null 2>&1; then
    echo "📦 Checking and installing Android dependencies (python, clang, git)..."
    pkg update -y || true
    pkg install -y python clang git make || true
fi

# Verify Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Error: python3 is not installed. Run 'pkg install python' in Termux first."
    exit 1
fi

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_PATH="$SRC_DIR/foxvc"
chmod +x "$BIN_PATH"

# 2. Compile native C VM for phone's CPU architecture (ARM64 / ARMv7 / x86_64)
echo "⚙️ Compiling native C VM engine for local Android CPU..."
CC_COMPILER="clang"
if ! command -v clang >/dev/null 2>&1; then
    CC_COMPILER="gcc"
fi

if command -v "$CC_COMPILER" >/dev/null 2>&1; then
    $CC_COMPILER -O3 -shared -fPIC "$SRC_DIR/engine/foxvm.c" -o "$SRC_DIR/engine/foxvm.so" -lm 2>/dev/null || true
    if [ -f "$SRC_DIR/engine/foxvm.so" ]; then
        echo "✓ Native ARM engine compiled successfully: $SRC_DIR/engine/foxvm.so"
    else
        echo "ℹ Native C library could not be built; Python VM will be used as fallback."
    fi
else
    echo "ℹ Compiler not found; Python VM fallback will be used."
fi

# 3. Target binary installation path
if [ "$IS_TERMUX" = true ]; then
    INSTALL_DIR="${PREFIX:-/data/data/com.termux/files/usr}/bin"
else
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
fi

echo "📦 Installing 'foxvc' executable into $INSTALL_DIR..."
ln -sf "$BIN_PATH" "$INSTALL_DIR/foxvc"
chmod +x "$INSTALL_DIR/foxvc"

# 4. PATH Verification
if ! echo "$PATH" | tr ":" "\n" | grep -qx "$INSTALL_DIR"; then
    SHELL_RC="$HOME/.bashrc"
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    fi
    if [ -f "$SHELL_RC" ]; then
        if ! grep -q "$INSTALL_DIR" "$SHELL_RC"; then
            echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$SHELL_RC"
        fi
    fi
fi

echo "============================================================"
echo "🎉 FoxVC is now installed locally on your Android device!"
echo "============================================================"
echo ""
echo "🚀 Quick Start Commands in Termux:"
echo "  1. Run a script:"
echo "     foxvc run examples/hello.fox"
echo ""
echo "  2. Compile to a standalone native Android binary:"
echo "     foxvc build examples/math.fox -o math_app"
echo "     ./math_app"
echo ""
echo "  3. Launch Local Offline Mobile Studio:"
echo "     foxvc mobile"
echo "     (Opens in your Android browser at http://localhost:8080)"
echo "============================================================"
