from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from .. import herramientas as h
from .. import puntos
from ..db import get_session
from ..models import Tienda

router = APIRouter(prefix="/cupones", tags=["cupones"])


class Lectura(BaseModel):
    codigo: str = Field(min_length=1, max_length=500, description="Texto leído del QR (de cliente o de cupón) o el código escrito.")


@router.post("/verificar")
def verificar(entrada: Lectura, db: Session = Depends(get_session)):
    """Consulta (sin canjear) los cupones de Paseo Points del QR que mostró el visitante."""
    datos = puntos.verificar_cupon(entrada.codigo)
    if datos.get("resultados"):
        tiendas = {h.normalizar(t.nombre): t for t in db.exec(select(Tienda)).all()}
        for cupon in (r for r in datos["resultados"] if r["tipo"] == "cupon"):
            t = tiendas.get(h.normalizar(cupon["nombre"] or ""))
            if t:
                cupon["tienda"] = {"id": t.id, "nombre": t.nombre, "piso": t.piso, "local": t.local, "sector": t.sector}
    return datos
