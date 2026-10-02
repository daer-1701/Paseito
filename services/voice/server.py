"""Private GPU service. WAV input; framed PCM output, one model load per process."""
import asyncio
import base64
from contextlib import asynccontextmanager
import io
import json
import logging
import os
import re
import threading
import time
import wave

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

log = logging.getLogger("uvicorn.error")
SAMPLE_RATE = 24000
MAX_AUDIO_BYTES = 1_000_000
MAX_PCM_BYTES = 8_000_000


def text_segments(text, limit=160):
    """Bound Spanish segments: Kokoro does not chunk long Spanish text itself."""
    for sentence in re.split(r"(?<=[.!?;:])\s+", text.strip()):
        pending = ""
        for word in sentence.split():
            if len(word) > limit:
                raise ValueError("word too long for speech")
            if pending and len(pending) + len(word) + 1 > limit:
                yield pending
                pending = ""
            pending = (pending + " " + word).strip()
        if pending:
            yield pending


def frame(payload):
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode()


def validate_wav(data):
    try:
        with wave.open(io.BytesIO(data), "rb") as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 16000):
                raise ValueError("expected mono PCM16 WAV at 16000 Hz")
            if not 0 < wav.getnframes() <= 15 * 16000:
                raise ValueError("expected 0–15 seconds of audio")
            if len(wav.readframes(wav.getnframes())) != wav.getnframes() * 2:
                raise ValueError("truncated WAV")
    except (wave.Error, EOFError) as exc:
        raise ValueError("invalid WAV") from exc


class Engine:
    def __init__(self):
        import numpy as np
        import torch
        from faster_whisper import WhisperModel
        from kokoro import KPipeline

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA unavailable. Check Windows NVIDIA driver and Docker WSL2 GPU support.")
        torch.set_num_threads(4)
        self.np = np
        self.lock = threading.Lock()
        self.voice = os.getenv("KOKORO_VOICE", "ef_dora")
        if self.voice not in {"ef_dora", "em_alex", "em_santa"}:
            raise ValueError("select an installed Spanish Kokoro voice")
        self.stt_model = os.getenv("WHISPER_MODEL", "small")
        self.stt = WhisperModel(self.stt_model, device="cuda", compute_type="int8_float16",
                               download_root="/models/whisper", num_workers=1, cpu_threads=4)
        self.tts = KPipeline(lang_code="e", repo_id="hexgrad/Kokoro-82M", device="cuda")
        # Download/cache the selected voice and run both models before readiness.
        list(self.tts("Hola, soy Jarvis.", voice=self.voice))
        segments, _ = self.stt.transcribe(np.zeros(16000, dtype=np.float32), language="es", beam_size=1)
        list(segments)
        log.info("Voice ready: GPU=%s, STT=%s, TTS=%s", torch.cuda.get_device_name(0), self.stt_model, self.voice)

    def transcribe(self, data):
        if not self.lock.acquire(blocking=False):
            raise HTTPException(503, "voice service busy; retry shortly", headers={"Retry-After": "1"})
        try:
            start = time.perf_counter()
            segments, _ = self.stt.transcribe(
                io.BytesIO(data), language="es", beam_size=1, condition_on_previous_text=False,
                vad_filter=True, initial_prompt="Paseo Aranjuez. Jarvis. PaseoYa. Paseo Points.")
            result = " ".join(segment.text.strip() for segment in segments).strip()[:2000]
            return {"text": result, "inference_ms": round((time.perf_counter() - start) * 1000)}
        finally:
            self.lock.release()

    def speech(self, parts, cancelled):
        start = time.perf_counter()
        size = 0
        # The first next() is awaited before sending HTTP 200; busy/error stays HTTP 503.
        if not self.lock.acquire(blocking=False):
            raise HTTPException(503, "voice service busy; retry shortly", headers={"Retry-After": "1"})
        try:
            for part in parts:
                if cancelled.is_set():
                    return
                for _, _, audio in self.tts(part, voice=self.voice):
                    if cancelled.is_set():
                        return
                    pcm = (self.np.clip(audio.numpy(), -1, 1) * 32767).astype("<i2").tobytes()
                    size += len(pcm)
                    if size > MAX_PCM_BYTES:
                        raise RuntimeError("speech exceeds output limit")
                    if pcm:
                        yield frame({"pcm": base64.b64encode(pcm).decode("ascii"), "sample_rate": SAMPLE_RATE})
            yield frame({"done": True, "inference_ms": round((time.perf_counter() - start) * 1000)})
        finally:
            self.lock.release()


@asynccontextmanager
async def lifespan(app):
    app.state.engine = await asyncio.to_thread(Engine)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health(request: Request):
    engine = request.app.state.engine
    return {"status": "ready", "device": "cuda", "stt": engine.stt_model, "voice": engine.voice}


@app.post("/transcribe")
async def transcribe(request: Request):
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > MAX_AUDIO_BYTES:
            raise HTTPException(413, "audio too large")
    try:
        validate_wav(data)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return await asyncio.to_thread(request.app.state.engine.transcribe, bytes(data))


class SpeechInput(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


def advance(iterator):
    # StopIteration cannot be transferred through an asyncio Future.
    return next(iterator, None)


@app.post("/speech")
async def speech(payload: SpeechInput, request: Request):
    try:
        parts = list(text_segments(payload.text))
        if not parts:
            raise ValueError("empty speech")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    cancelled = threading.Event()
    iterator = request.app.state.engine.speech(parts, cancelled)

    async def next_frame():
        # Finish an active inference before closing its generator on disconnect.
        work = asyncio.create_task(asyncio.to_thread(advance, iterator))
        try:
            return await asyncio.shield(work)
        except asyncio.CancelledError:
            cancelled.set()
            await work
            iterator.close()
            raise

    first = await next_frame()

    async def output():
        try:
            current = first
            while current is not None:
                yield current
                current = await next_frame()
        except Exception:
            log.exception("Speech stream failed")
            yield frame({"error": "speech interrupted"})
        finally:
            cancelled.set()
            iterator.close()

    return StreamingResponse(output(), media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})
