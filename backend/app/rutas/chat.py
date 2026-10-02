import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from .. import agente
from ..db import get_session

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatEntrada(BaseModel):
    mensaje: str = Field(min_length=1, max_length=1000)
    session_id: Optional[str] = Field(
        default=None, description="Omitir en el primer mensaje; reutilizar el que devuelve la API."
    )


class ChatSalida(BaseModel):
    session_id: str
    respuesta: str = Field(description="Texto para mostrar y leer en voz alta.")
    tarjetas: list[dict[str, Any]] = Field(
        description="Datos estructurados para la UI. Campo 'tipo': lugar | producto | promocion | evento | info."
    )
    herramientas: list[dict[str, Any]]
    modelo: str
    duracion_ms: int


@router.post("", response_model=ChatSalida)
def chatear(entrada: ChatEntrada, db: Session = Depends(get_session)):
    session_id = entrada.session_id or uuid.uuid4().hex
    try:
        return agente.responder(session_id, entrada.mensaje.strip(), db)
    except agente.IANoConfigurada as e:
        raise HTTPException(status_code=503, detail=str(e))
    except agente.ErrorIA as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{session_id}", status_code=204)
def reiniciar(session_id: str):
    """Olvida la conversación (p. ej. cuando un nuevo visitante se acerca al kiosco)."""
    agente.reiniciar_sesion(session_id)
