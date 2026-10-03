"""Speech adapters with optional OpenAI TTS and a local fallback."""

from __future__ import annotations

import importlib.util
import base64
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
import wave
from pathlib import Path


MAX_AUDIO_BYTES = 1_000_000
MAX_SECONDS = 15
MAX_TTS_BYTES = 8_000_000
MODEL_DIR = Path(__file__).resolve().parents[1] / "models"


class VoiceUnavailable(RuntimeError):
    pass


def status() -> dict:
    service = os.getenv("JARVIS_VOICE_URL", "").rstrip("/")
    if os.getenv("JARVIS_TTS_PROVIDER") == "gpu":
        ready = False
        try:
            with urllib.request.urlopen(service + "/health", timeout=2) as response:
                ready = json.loads(response.read(4096)).get("status") == "ready"
        except (OSError, ValueError):
            pass
        return {"transcription": ready, "synthesis": "gpu" if ready else "browser",
                "ready": ready, "streaming": ready, "prefer_server_stt": True,
                "silence_ms": 650, "max_recording_seconds": MAX_SECONDS}
    whisper = os.getenv("JARVIS_WHISPER_BIN") or shutil.which("whisper-cli")
    model = os.getenv("JARVIS_WHISPER_MODEL", str(MODEL_DIR / "ggml-base.bin"))
    piper_model = os.getenv("JARVIS_PIPER_MODEL", str(MODEL_DIR / "es_MX-ald-medium.onnx"))
    piper_ready = bool(piper_model and Path(piper_model).is_file() and
                       importlib.util.find_spec("piper"))
    say_ready = bool(shutil.which("say") and shutil.which("afconvert"))
    provider = os.getenv("JARVIS_TTS_PROVIDER", "local").lower()
    openai_ready = bool(os.getenv("OPENAI_API_KEY"))
    local_synthesis = "piper" if piper_ready else ("system" if say_ready else "browser")
    synthesis = 'edge' if provider == 'edge' else "openai" if provider in {"openai", "auto"} and openai_ready else local_synthesis
    return {
        "transcription": bool(whisper and model and Path(model).is_file()),
        "synthesis": synthesis,
        "synthesis_fallback": local_synthesis if synthesis == "openai" else None,
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
                if len(wav.readframes(wav.getnframes())) != wav.getnframes() * 2:
                    raise ValueError("truncated WAV audio")
        except wave.Error as exc:
            raise ValueError("invalid WAV audio") from exc


def transcribe(data: bytes) -> str:
    _validate_wav(data)
    service = os.getenv("JARVIS_VOICE_URL", "").rstrip("/")
    if service:
        request = urllib.request.Request(service + "/transcribe", data=data,
                                         headers={"Content-Type": "audio/wav"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read(16384))
            if not isinstance(result.get("text"), str):
                raise ValueError("invalid transcription")
            return result["text"][:2000]
        except (OSError, ValueError) as exc:
            raise VoiceUnavailable("GPU transcription unavailable or busy") from exc
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


def _speakable(text: str) -> str:
    """Remove presentational Markdown before passing text to a speech engine."""
    text = re.sub(r"[*_`#]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _openai_synthesize(text: str) -> tuple[bytes, str]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise VoiceUnavailable("OPENAI_API_KEY is not configured")
    body = {
        "model": os.getenv("JARVIS_OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        "voice": os.getenv("JARVIS_OPENAI_TTS_VOICE", "marin"),
        "input": text,
        "instructions": os.getenv(
            "JARVIS_OPENAI_TTS_INSTRUCTIONS",
            "Habla en español latino claro y cálido. Eres Jarvis, asistente del Paseo Aranjuez en Cochabamba. "
            "Mantén un ritmo natural, amable y profesional; pronuncia nombres de negocios con claridad.",
        ),
        "response_format": "wav",
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech", data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            audio = response.read(MAX_TTS_BYTES + 1)
            mime = response.headers.get_content_type() or "audio/wav"
        if not audio or len(audio) > MAX_TTS_BYTES:
            raise VoiceUnavailable("OpenAI speech response was empty or too large")
        return audio, mime
    except (OSError, urllib.error.HTTPError, urllib.error.URLError, ValueError) as exc:
        raise VoiceUnavailable("OpenAI speech synthesis failed") from exc


def _local_synthesize(text: str) -> tuple[bytes, str]:
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


def synthesize(text: str) -> tuple[bytes, str]:
    if not isinstance(text, str) or not 0 < len(text.strip()) <= 2000:
        raise ValueError("text must contain 1 to 2000 characters")
    spoken = _speakable(text)
    provider = os.getenv("JARVIS_TTS_PROVIDER", "local").lower()
    if provider == "gpu":
        return _gpu_wav(spoken)
    if provider == 'edge':
        import asyncio
        import edge_tts
        async def collect():
            data = bytearray()
            async for chunk in edge_tts.Communicate(spoken, os.getenv('EDGE_TTS_VOZ','es-BO-SofiaNeural'),
                                                   rate=os.getenv('EDGE_TTS_VELOCIDAD','+0%')).stream():
                if chunk['type'] == 'audio': data.extend(chunk['data'])
                if len(data)>MAX_TTS_BYTES: raise VoiceUnavailable('speech too large')
            if not data: raise VoiceUnavailable('empty speech')
            return bytes(data), 'audio/mpeg'
        try:
            return asyncio.run(asyncio.wait_for(collect(), timeout=8))
        except Exception as exc:
            raise VoiceUnavailable('Edge speech unavailable; browser voice remains available') from exc
    if provider not in {"local", "openai", "auto"}:
        raise ValueError("JARVIS_TTS_PROVIDER must be local, openai, auto or gpu")
    if provider in {"openai", "auto"} and os.getenv("OPENAI_API_KEY"):
        try:
            return _openai_synthesize(spoken)
        except VoiceUnavailable:
            if os.getenv("JARVIS_TTS_STRICT_OPENAI") == "1":
                raise
    return _local_synthesize(spoken)


def stream_speech(text):
    """Forward framed PCM as it arrives; closing the generator closes upstream."""
    if not isinstance(text, str) or not 0 < len(text.strip()) <= 2000:
        raise ValueError("text must contain 1 to 2000 characters")
    service = os.getenv("JARVIS_VOICE_URL", "").rstrip("/")
    if not service or os.getenv("JARVIS_TTS_PROVIDER") != "gpu":
        raise VoiceUnavailable("streaming requires the GPU voice service")
    request = urllib.request.Request(service + "/speech", method="POST",
        data=json.dumps({"text": _speakable(text)}).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.headers.get_content_type() != "application/x-ndjson":
                raise VoiceUnavailable("unexpected speech stream format")
            total = 0
            while True:
                chunk = response.read1(8192)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_TTS_BYTES * 2:
                    raise VoiceUnavailable("speech stream too large")
                yield chunk
    except OSError as exc:
        raise VoiceUnavailable("GPU speech unavailable or busy") from exc


def _gpu_wav(text):
    """Compatibility for clients that still request a complete WAV."""
    pending = b""
    pcm = bytearray()
    done = False
    for chunk in stream_speech(text):
        pending += chunk
        while b"\n" in pending:
            line, pending = pending.split(b"\n", 1)
            event = json.loads(line)
            if event.get("error"):
                raise VoiceUnavailable("speech stream interrupted")
            if "pcm" in event:
                if event.get("sample_rate") != 24000:
                    raise VoiceUnavailable("unexpected sample rate")
                pcm.extend(base64.b64decode(event["pcm"], validate=True))
                if len(pcm) > MAX_TTS_BYTES:
                    raise VoiceUnavailable("speech too large")
            done = done or event.get("done", False)
    if not done or not pcm or len(pcm) % 2:
        raise VoiceUnavailable("incomplete speech stream")
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
        wav.writeframes(pcm)
    return output.getvalue(), "audio/wav"
