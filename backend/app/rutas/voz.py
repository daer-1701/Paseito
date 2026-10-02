from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .. import voz
from ..agente import ErrorIA, IANoConfigurada

router = APIRouter(prefix="/voz", tags=["voz"])


class VozEntrada(BaseModel):
    texto: str = Field(min_length=1, max_length=800, description="Normalmente el campo 'respuesta' de /chat.")
    voz: Optional[str] = Field(
        default=None, description="Opcional. Con edge: es-BO-SofiaNeural, es-BO-MarceloNeural… Con gemini: Kore, Puck…"
    )


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
