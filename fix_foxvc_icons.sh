#!/bin/bash
set -u

FOXVC="${HOME}/Desktop/FoxVC"
if [ ! -d "$FOXVC" ]; then
    FOXVC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

ICON_SRC="$FOXVC/assets/foxvc-icon.png"
ICON_ROOT="$HOME/.local/share/icons/hicolor"
APP_DIR="$HOME/.local/share/applications"
MIME_DIR="$HOME/.local/share/mime"
MIME_FILE="$HOME/.local/share/mime/packages/foxvc.xml"
DESKTOP_FILE="$APP_DIR/foxvc-studio.desktop"

echo "========================================"
echo "       FOXVC ICON INTEGRATION FIX"
echo "========================================"
echo

echo "[1/8] Checking source icon..."
if [ ! -f "$ICON_SRC" ]; then
    python3 "$FOXVC/create_foxvc_icon.py" 2>/dev/null || true
fi

if [ ! -f "$ICON_SRC" ]; then
    echo "ERROR: $ICON_SRC does not exist."
    exit 1
fi
file "$ICON_SRC"

echo
echo "[2/8] Installing application and MIME icons..."
for SIZE in 48 64 128 256; do
    mkdir -p "$ICON_ROOT/${SIZE}x${SIZE}/apps"
    mkdir -p "$ICON_ROOT/${SIZE}x${SIZE}/mimetypes"
    python3 - "$ICON_SRC" "$ICON_ROOT/${SIZE}x${SIZE}/apps/foxvc-studio.png" "$ICON_ROOT/${SIZE}x${SIZE}/mimetypes/text-x-fox.png" "$SIZE" <<'PY'
from PIL import Image
import sys
src, app_out, mime_out, size = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
img = Image.open(src).convert("RGBA")
img = img.resize((size, size), Image.Resampling.LANCZOS)
img.save(app_out, "PNG")
img.save(mime_out, "PNG")
PY
done

mkdir -p "$ICON_ROOT/scalable/apps"
mkdir -p "$ICON_ROOT/scalable/mimetypes"
python3 - "$ICON_SRC" "$ICON_ROOT/scalable/apps/foxvc-studio.png" "$ICON_ROOT/scalable/mimetypes/text-x-fox.png" <<'PY'
from PIL import Image
import sys
src, app_out, mime_out = sys.argv[1], sys.argv[2], sys.argv[3]
img = Image.open(src).convert("RGBA")
img.save(app_out, "PNG")
img.save(mime_out, "PNG")
PY
echo "Icons installed."

echo
echo "[3/8] Writing FoxVC desktop launcher..."
mkdir -p "$APP_DIR"
cat <<EOF_DESKTOP > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=FoxVC Studio
Comment=FoxVC Development Environment
Exec=python3 $FOXVC/run_studio.py %f
Icon=foxvc-studio
Terminal=false
Categories=Development;Programming;
MimeType=text/x-fox;
StartupNotify=true
EOF_DESKTOP
chmod +x "$DESKTOP_FILE"
echo "Desktop launcher written."

echo
echo "[4/8] Writing FoxVC MIME definition..."
mkdir -p "$MIME_DIR/packages"
cat <<'EOF_MIME' > "$MIME_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="text/x-fox">
    <comment>FoxVC Source Code</comment>
    <glob pattern="*.fox"/>
    <icon name="text-x-fox"/>
  </mime-type>
</mime-info>
EOF_MIME
echo "MIME definition written."

echo
echo "[5/8] Registering MIME and desktop databases..."
update-mime-database "$MIME_DIR" 2>/dev/null || true
update-desktop-database "$APP_DIR" 2>/dev/null || true
echo "Databases updated."

echo
echo "[6/8] Detecting TDE cache tools..."
KBUILD=""
for candidate in     "$(command -v kbuildsycoca 2>/dev/null || true)"     "/opt/trinity/bin/kbuildsycoca"     "/opt/trinity/bin/kbuildsycoca4"     "/usr/bin/kbuildsycoca"     "/usr/bin/kbuildsycoca4"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
        KBUILD="$candidate"
        break
    fi
done

if [ -n "$KBUILD" ]; then
    echo "Found: $KBUILD"
    "$KBUILD" --noincremental 2>/dev/null || "$KBUILD" 2>/dev/null || true
else
    echo "No kbuildsycoca executable found."
    echo "Continuing with TDE desktop refresh."
fi

echo
echo "[7/8] Refreshing TDE desktop..."
if command -v kdesktop >/dev/null 2>&1; then
    echo "Restarting kdesktop..."
    kdesktop --replace >/tmp/foxvc-kdesktop.log 2>&1 &
elif [ -x /opt/trinity/bin/kdesktop ]; then
    echo "Restarting /opt/trinity/bin/kdesktop..."
    /opt/trinity/bin/kdesktop --replace >/tmp/foxvc-kdesktop.log 2>&1 &
else
    echo "kdesktop executable not found."
fi
sleep 1

echo
echo "[8/8] Verifying installation..."
echo
echo "--- MIME association ---"
xdg-mime query default text/x-fox 2>/dev/null || true

echo
echo "--- File MIME type ---"
if [ -f "$FOXVC/examples/physics.fox" ]; then
    xdg-mime query filetype "$FOXVC/examples/physics.fox" 2>/dev/null || true
else
    echo "No physics.fox example found; checking a .fox file instead..."
    FIRST_FOX="$(find "$FOXVC" -type f -name '*.fox' -print -quit)"
    if [ -n "$FIRST_FOX" ]; then
        xdg-mime query filetype "$FIRST_FOX" 2>/dev/null || true
    fi
fi

echo
echo "--- Desktop launcher ---"
grep -E '^(Name|Exec|Icon|MimeType)=' "$DESKTOP_FILE" 2>/dev/null || true

echo
echo "--- MIME definition ---"
cat "$MIME_FILE"

echo
echo "--- Source icon ---"
file "$ICON_SRC"

echo
echo "========================================"
echo "       FOXVC ICON FIX COMPLETE"
echo "========================================"
