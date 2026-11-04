"""
FoxVC Audio & Sound Shelf (shelves/audio.py).
Provides native sound effects, frequency tone synthesis, PCM WAV generation,
and audio playback hooks.
"""

import math
import wave
import struct
import tempfile
import os
import shutil
import subprocess
from typing import Dict, Any, List, Optional
from .common import SecurityPolicy


def fox_synth_sine(freq: float = 440.0, duration_sec: float = 0.5, volume: float = 0.5, sample_rate: int = 44100) -> List[float]:
    """Generates pure sine wave PCM samples normalized between -1.0 and 1.0."""
    total_samples = int(float(sample_rate) * float(duration_sec))
    samples = []
    f = float(freq)
    vol = max(0.0, min(1.0, float(volume)))
    for i in range(total_samples):
        t = i / sample_rate
        val = math.sin(2.0 * math.pi * f * t) * vol
        samples.append(val)
    return samples


def fox_save_wav(filepath: str, samples: List[float], sample_rate: int = 44100) -> int:
    """Exports raw float PCM samples (-1.0 to 1.0) into a standard 16-bit Mono WAV file."""
    try:
        sr = int(sample_rate)
        with wave.open(filepath, "w") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sr)
            packed_frames = []
            for s in samples:
                clamped = max(-1.0, min(1.0, float(s)))
                sample_int = int(clamped * 32767.0)
                packed_frames.append(struct.pack("<h", sample_int))
            wav_file.writeframes(b"".join(packed_frames))
        return 1
    except Exception as e:
        return 0


def fox_play_tone(freq: float = 440.0, duration_ms: float = 300.0, volume: float = 0.5) -> int:
    """Synthesizes and immediately plays a frequency tone through system audio."""
    dur_sec = max(0.05, float(duration_ms) / 1000.0)
    samples = fox_synth_sine(freq=float(freq), duration_sec=dur_sec, volume=float(volume))

    # Write temporary wav and play via aplay / paplay / afplay if available
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        ok = fox_save_wav(tmp_path, samples)
        if not ok:
            return 0

        player = shutil.which("paplay") or shutil.which("aplay") or shutil.which("afplay")
        if player:
            subprocess.Popen([player, tmp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return 1
        return 1
    except Exception:
        return 0


def fox_play_wav(filepath: str) -> int:
    """Plays an existing .wav audio file asynchronously."""
    if not os.path.exists(filepath):
        return 0
    player = shutil.which("paplay") or shutil.which("aplay") or shutil.which("afplay")
    if player:
        try:
            subprocess.Popen([player, filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return 1
        except Exception:
            return 0
    return 0


def get_audio_shelf(policy: Optional[SecurityPolicy] = None) -> Dict[str, Any]:
    return {
        "playTone": fox_play_tone,
        "playWav": fox_play_wav,
        "synthSine": fox_synth_sine,
        "saveWav": fox_save_wav,
    }
