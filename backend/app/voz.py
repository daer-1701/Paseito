import base64
import logging
import time
from collections import OrderedDict
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

import edge_tts
from fastapi.concurrency import run_in_threadpool
from google.genai import types

from .agente import ErrorIA, IANoConfigurada, _cliente, _es_transitorio, _modelos_disponibles
from .config import (
    EDGE_TTS_VELOCIDAD, EDGE_TTS_VOZ, GEMINI_TTS_MODELS, GEMINI_TTS_TIMEOUT_S, GEMINI_TTS_VOZ, TTS_MOTOR,
)

log = logging.getLogger("jarvis")

ESTILO_GEMINI = "Lee en español latinoamericano, con voz cálida, amable y a ritmo natural: "
PROMPT_TRANSCRIPCION = (
    "Transcribe exactamente lo que dice la persona (español de Bolivia; habla con la asistente del Paseo Aranjuez). "
    "Devuelve solo el texto, sin comillas ni comentarios. Si no se entiende nada o solo hay ruido, devuelve vacío."
)
MAX_CACHE = 64

# (motor, voz, texto) -> (mp3, origen). Los saludos y respuestas frecuentes no se vuelven a generar.
_cache: OrderedDict[tuple[str, str, str], tuple[bytes, str]] = OrderedDict()
_hilos = ThreadPoolExecutor(max_workers=16, thread_name_prefix="tts")


async def sintetizar(texto: str, voz: str | None = None) -> tuple[bytes, str]:
    """Convierte texto a MP3 con el motor configurado. Devuelve (audio, origen)."""
    voz = voz or (EDGE_TTS_VOZ if TTS_MOTOR == "edge" else GEMINI_TTS_VOZ)
    clave = (TTS_MOTOR, voz, texto)
    if clave in _cache:
        _cache.move_to_end(clave)
        return _cache[clave]

    if TTS_MOTOR == "edge":
        resultado = await _edge(texto, voz)
    else:
        resultado = await run_in_threadpool(_gemini_carrera, texto, voz)

    _cache[clave] = resultado
    if len(_cache) > MAX_CACHE:
        _cache.popitem(last=False)
    return resultado


async def _edge(texto: str, voz: str) -> tuple[bytes, str]:
    inicio = time.perf_counter()
    audio = bytearray()
    try:
        async for trozo in edge_tts.Communicate(texto, voz, rate=EDGE_TTS_VELOCIDAD).stream():
            if trozo["type"] == "audio":
                audio.extend(trozo["data"])
    except Exception as e:
        raise ErrorIA(f"No se pudo generar la voz: {str(e)[:200]}") from e
    if not audio:
        raise ErrorIA("El servicio de voz no devolvió audio")
    log.info("TTS edge %s en %.1fs", voz, time.perf_counter() - inicio)
    return bytes(audio), f"edge:{voz}"


def _gemini(modelo: str, texto: str, voz: str) -> bytes:
    interaccion = _cliente.interactions.create(
        model=modelo,
        input=ESTILO_GEMINI + texto,
        response_modalities=["audio"],
        response_format={"type": "audio", "mime_type": "audio/mp3"},
        generation_config={"speech_config": {"voice": voz, "language": "es-419"}},
        timeout=GEMINI_TTS_TIMEOUT_S,
    )
    for paso in interaccion.steps or []:
        for item in getattr(paso, "content", None) or []:
            if getattr(item, "type", None) == "audio" and item.data:
                return item.data if isinstance(item.data, bytes) else base64.b64decode(item.data)
    raise ErrorIA(f"{modelo} no devolvió audio")


def _gemini_carrera(texto: str, voz: str) -> tuple[bytes, str]:
    """Lanza todos los modelos de Gemini TTS a la vez y se queda con el primero que responde."""
    if _cliente is None:
        raise IANoConfigurada("Falta GEMINI_API_KEY en backend/.env")

    inicio = time.perf_counter()
    pendientes = {_hilos.submit(_gemini, m, texto, voz): m for m in GEMINI_TTS_MODELS}
    error: Exception | None = None
    while pendientes:
        listos, _ = wait(pendientes, return_when=FIRST_COMPLETED)
        for futuro in listos:
            modelo = pendientes.pop(futuro)
            try:
                audio = futuro.result()
            except Exception as e:
                error = e
                log.warning("TTS %s falló (%s)", modelo, type(e).__name__)
                continue
            # Los que siguen corriendo terminan en segundo plano y su resultado se descarta.
            log.info("TTS ganó %s en %.1fs", modelo, time.perf_counter() - inicio)
            return audio, modelo

    raise ErrorIA(f"No se pudo generar la voz: {str(error)[:200]}") from error


def transcribir(audio: bytes, mime: str) -> tuple[str, str]:
    """Pasa a texto lo que dijo el visitante. Devuelve (texto, modelo)."""
    if _cliente is None:
        raise IANoConfigurada("Falta GEMINI_API_KEY en backend/.env")

    error: Exception | None = None
    for modelo in _modelos_disponibles(None):
        inicio = time.perf_counter()
        try:
            respuesta = _cliente.models.generate_content(
                model=modelo,
                contents=[types.Part.from_bytes(data=audio, mime_type=mime), PROMPT_TRANSCRIPCION],
                config=types.GenerateContentConfig(
                    temperature=0,
                    thinking_config=types.ThinkingConfig(thinking_level="low"),
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
        except Exception as e:
            error = e
            if not _es_transitorio(e):
                break
            log.warning("Transcripción con %s falló (%s)", modelo, type(e).__name__)
            continue
        texto = (respuesta.text or "").strip().strip('"«»').strip()
        log.info("STT %s en %.1fs: %r", modelo, time.perf_counter() - inicio, texto[:80])
        return texto, modelo

    raise ErrorIA(f"No se pudo transcribir el audio: {str(error)[:200]}") from error
