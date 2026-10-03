import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .. import voz
from ..agente import ErrorIA, IANoConfigurada

router = APIRouter(prefix="/voz", tags=["voz"])

MAX_AUDIO_BYTES = 5 * 1024 * 1024


class VozEntrada(BaseModel):
    texto: str = Field(min_length=1, max_length=800, description="Normalmente el campo 'respuesta' de /chat.")
    voz: Optional[str] = Field(
        default=None, description="Opcional. Con edge: es-BO-SofiaNeural, es-BO-MarceloNeural… Con gemini: Kore, Puck…"
    )


class Transcripcion(BaseModel):
    texto: str
    modelo: str
    duracion_ms: int


@router.post("", response_class=Response, responses={200: {"content": {"audio/mpeg": {}}}})
async def hablar(entrada: VozEntrada):
    """Devuelve la respuesta hablada en MP3. La cabecera X-Modelo-Voz indica qué motor/voz la generó."""
    try:
        audio, origen = await voz.sintetizar(entrada.texto.strip(), entrada.voz)
    except IANoConfigurada as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ErrorIA as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=audio, media_type="audio/mpeg", headers={"X-Modelo-Voz": origen})


@router.post("/escuchar", response_model=Transcripcion)
async def escuchar(request: Request):
    """Transcribe con Gemini el audio del cuerpo (audio/wav, audio/mp3, audio/ogg…).

    Respaldo para navegadores sin reconocimiento de voz propio. Si no se entendió nada, `texto` llega vacío.
    """
    mime = request.headers.get("content-type", "").split(";")[0].strip()
    if not mime.startswith("audio/"):
        raise HTTPException(status_code=415, detail="Envía el audio con Content-Type audio/wav, audio/mp3…")
    audio = await request.body()
    if not audio:
        raise HTTPException(status_code=400, detail="No llegó audio")
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio demasiado largo")

    inicio = time.perf_counter()
    try:
        texto, modelo = await run_in_threadpool(voz.transcribir, audio, mime)
    except IANoConfigurada as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ErrorIA as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Transcripcion(texto=texto, modelo=modelo, duracion_ms=int((time.perf_counter() - inicio) * 1000))
