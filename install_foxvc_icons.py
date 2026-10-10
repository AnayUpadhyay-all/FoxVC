from pathlib import Path
from PIL import Image
import shutil
import subprocess

root = Path.home() / "Desktop" / "FoxVC"
if not root.exists():
    root = Path(__file__).resolve().parent

source = root / "assets" / "foxvc-icon.png"
if not source.exists():
    create_script = root / "create_foxvc_icon.py"
    if create_script.exists():
        subprocess.run(["python3", str(create_script)], check=False)

if not source.exists():
    raise SystemExit(f"ERROR: Missing {source}")

img = Image.open(source)
img.verify()
img = Image.open(source).convert("RGBA")

icon_root = Path.home() / ".local" / "share" / "icons" / "hicolor"
sizes = [48, 64, 128, 256]

for size in sizes:
    apps_dir = icon_root / f"{size}x{size}" / "apps"
    mime_dir = icon_root / f"{size}x{size}" / "mimetypes"
    apps_dir.mkdir(parents=True, exist_ok=True)
    mime_dir.mkdir(parents=True, exist_ok=True)

    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(apps_dir / "foxvc-studio.png", "PNG")
    resized.save(mime_dir / "text-x-fox.png", "PNG")

desktop = Path.home() / ".local" / "share" / "applications" / "foxvc-studio.desktop"
if desktop.exists():
    text = desktop.read_text()
    lines = text.splitlines()
    output = []
    found = False
    for line in lines:
        if line.startswith("Icon="):
            output.append("Icon=foxvc-studio")
            found = True
        else:
            output.append(line)
    if not found:
        output.append("Icon=foxvc-studio")
    desktop.write_text("\n".join(output) + "\n")

mime = Path.home() / ".local" / "share" / "mime" / "packages" / "foxvc.xml"
if mime.exists():
    text = mime.read_text()
    if "<icon name=" not in text:
        text = text.replace(
            "<comment>FoxVC Source Code</comment>",
            "<comment>FoxVC Source Code</comment>\n"
            "      <icon name=\"text-x-fox\"/>"
        )
        mime.write_text(text)

if shutil.which("update-mime-database"):
    subprocess.run(
        ["update-mime-database", str(Path.home() / ".local" / "share" / "mime")],
        check=False
    )
if shutil.which("update-desktop-database"):
    subprocess.run(
        ["update-desktop-database", str(Path.home() / ".local" / "share" / "applications")],
        check=False
    )

print("FoxVC icons installed successfully.")
print("Application icon: foxvc-studio")
print("FoxVC file icon: text-x-fox")
