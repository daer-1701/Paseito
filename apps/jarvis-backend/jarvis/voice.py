"""Optional local speech recognition and synthesis adapters."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path


MAX_AUDIO_BYTES = 1_000_000
MAX_SECONDS = 15
MODEL_DIR = Path(__file__).resolve().parents[1] / "models"


class VoiceUnavailable(RuntimeError):
    pass


def status() -> dict:
    whisper = os.getenv("JARVIS_WHISPER_BIN") or shutil.which("whisper-cli")
    model = os.getenv("JARVIS_WHISPER_MODEL", str(MODEL_DIR / "ggml-base.bin"))
    piper_model = os.getenv("JARVIS_PIPER_MODEL", str(MODEL_DIR / "es_MX-ald-medium.onnx"))
    piper_ready = bool(piper_model and Path(piper_model).is_file() and
                       importlib.util.find_spec("piper"))
    say_ready = bool(shutil.which("say") and shutil.which("afconvert"))
    return {
        "transcription": bool(whisper and model and Path(model).is_file()),
        "synthesis": "piper" if piper_ready else ("system" if say_ready else "browser"),
        "max_recording_seconds": MAX_SECONDS,
    }


def _validate_wav(data: bytes) -> None:
    if not 44 <= len(data) <= MAX_AUDIO_BYTES:
        raise ValueError("audio must be a short PCM WAV recording")
    with tempfile.TemporaryFile() as audio:
        audio.write(data)
        audio.seek(0)
        try:
            with wave.open(audio, "rb") as wav:
                if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 16000):
                    raise ValueError("audio must be mono 16-bit PCM at 16 kHz")
                if not 0 < wav.getnframes() / 16000 <= MAX_SECONDS:
                    raise ValueError("audio duration must be between 0 and 15 seconds")
        except wave.Error as exc:
            raise ValueError("invalid WAV audio") from exc


def transcribe(data: bytes) -> str:
    _validate_wav(data)
    whisper = os.getenv("JARVIS_WHISPER_BIN") or shutil.which("whisper-cli")
    model = os.getenv("JARVIS_WHISPER_MODEL", str(MODEL_DIR / "ggml-base.bin"))
    if not whisper or not model or not Path(model).is_file():
        raise VoiceUnavailable("configure JARVIS_WHISPER_MODEL with a multilingual Whisper model")
    with tempfile.TemporaryDirectory(prefix="jarvis-stt-") as directory:
        audio_path = Path(directory) / "input.wav"
        output_base = Path(directory) / "transcript"
        audio_path.write_bytes(data)
        command = [whisper, "-m", model, "-f", str(audio_path),
                   "-l", "es", "--prompt",
                   os.getenv("JARVIS_WHISPER_PROMPT", "Paseo Aranjuez. Jarvis. PaseoYa. Paseo Points."),
                   "-otxt", "-of", str(output_base), "-np"]
        if os.getenv("JARVIS_WHISPER_GPU") != "1":
            command.append("-ng")
        try:
            subprocess.run(command, check=True, timeout=45, capture_output=True)
            return output_base.with_suffix(".txt").read_text(encoding="utf-8").strip()[:2000]
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise VoiceUnavailable("local transcription failed") from exc


def synthesize(text: str) -> tuple[bytes, str]:
    if not isinstance(text, str) or not 0 < len(text.strip()) <= 2000:
        raise ValueError("text must contain 1 to 2000 characters")
    piper_model = os.getenv("JARVIS_PIPER_MODEL", str(MODEL_DIR / "es_MX-ald-medium.onnx"))
    piper_ready = bool(piper_model and Path(piper_model).is_file() and
                       importlib.util.find_spec("piper"))
    say = shutil.which("say")
    afconvert = shutil.which("afconvert")
    with tempfile.TemporaryDirectory(prefix="jarvis-tts-") as directory:
        if piper_ready:
            output = Path(directory) / "speech.wav"
            command = [os.sys.executable, "-m", "piper", "-m", piper_model,
                       "-f", str(output), "--", text]
            mime = "audio/wav"
        elif say and afconvert:
            aiff = Path(directory) / "speech.aiff"
            output = Path(directory) / "speech.wav"
            command = [say, "-v", os.getenv("JARVIS_SYSTEM_VOICE", "Mónica"),
                       "-o", str(aiff), text]
            mime = "audio/wav"
        else:
            raise VoiceUnavailable("no local speech synthesizer is available")
        try:
            subprocess.run(command, check=True, timeout=35, capture_output=True)
            if not piper_ready:
                subprocess.run([afconvert, "-f", "WAVE", "-d", "LEI16",
                                str(aiff), str(output)], check=True, timeout=15,
                               capture_output=True)
            audio = output.read_bytes()
            if len(audio) <= 44:
                raise VoiceUnavailable("local speech synthesizer returned empty audio")
            return audio, mime
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise VoiceUnavailable("local speech synthesis failed") from exc
