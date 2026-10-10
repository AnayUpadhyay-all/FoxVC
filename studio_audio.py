import os
import shutil
import subprocess
import threading

SUPPORTED_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aac', '.opus'}
PREFERRED_KEYWORDS = ['welcome', 'startup', 'intro', 'greeting']

def get_assets_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, 'assets')
    if not os.path.exists(assets_dir):
        try:
            os.makedirs(assets_dir, exist_ok=True)
        except OSError:
            pass
    return assets_dir

def discover_startup_audio(assets_dir=None):
    if assets_dir is None:
        assets_dir = get_assets_dir()

    if not os.path.isdir(assets_dir):
        return None

    try:
        entries = os.listdir(assets_dir)
    except OSError as e:
        print(f"[FoxVC Startup Audio] Cannot read assets directory: {e}")
        return None

    # Collect valid audio files
    candidates = []
    for entry in entries:
        full_path = os.path.join(assets_dir, entry)
        if os.path.isfile(full_path):
            _, ext = os.path.splitext(entry)
            if ext.lower() in SUPPORTED_EXTENSIONS:
                candidates.append(entry)

    if not candidates:
        return None

    if len(candidates) == 1:
        return os.path.join(assets_dir, candidates[0])

    # Deterministic multi-file selection
    # Priority 1: Keyword match in filename
    for kw in PREFERRED_KEYWORDS:
        matching = sorted([f for f in candidates if kw in f.lower()])
        if matching:
            selected = matching[0]
            print(f"[FoxVC Startup Audio] Multiple audio files found. Selected priority match: {selected}")
            return os.path.join(assets_dir, selected)

    # Priority 2: Alphabetical sort fallback
    candidates.sort()
    selected = candidates[0]
    print(f"[FoxVC Startup Audio] Multiple audio files found. Selected alphabetical first: {selected}")
    return os.path.join(assets_dir, selected)

def _get_player_command(file_path):
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    # Tool detection order
    if shutil.which("pw-play"):
        return ["pw-play", file_path]
    if shutil.which("paplay") and ext in ('.wav', '.ogg', '.flac'):
        return ["paplay", file_path]
    if ext == '.wav' and shutil.which("aplay"):
        return ["aplay", "-q", file_path]
    if shutil.which("ffplay"):
        return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path]
    if shutil.which("play"):
        return ["play", "-q", file_path]

    return None

def _play_worker(file_path):
    cmd = _get_player_command(file_path)
    if not cmd:
        print(f"[FoxVC Startup Audio] No compatible audio player found on system (checked pw-play, paplay, aplay, ffplay, play).")
        return

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        proc.wait()
    except Exception as e:
        print(f"[FoxVC Startup Audio] Playback failed: {e}\nStudio startup continues normally.")

def play_startup_audio_async():
    try:
        audio_file = discover_startup_audio()
        if not audio_file:
            print("[FoxVC Startup Audio] No startup audio found in assets/.")
            return

        rel_path = os.path.relpath(audio_file, os.path.dirname(os.path.abspath(__file__)))
        print(f"[FoxVC Startup Audio] Playing: {rel_path}")

        # Non-blocking daemon thread so UI never freezes
        t = threading.Thread(target=_play_worker, args=(audio_file,), daemon=True)
        t.start()
    except Exception as e:
        print(f"[FoxVC Startup Audio] Unexpected error during audio discovery: {e}\nStudio startup continues normally.")
