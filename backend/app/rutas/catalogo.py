from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from .. import herramientas as h
from ..db import get_session
from ..models import Faq, Producto, Promocion, Tienda

router = APIRouter(tags=["catálogo"])


@router.get("/lugares")
def listar_lugares(q: str = "", tipo: str = "", solo_abiertos: bool = False,
                   db: Session = Depends(get_session)):
    if not q:
        tiendas = db.exec(select(Tienda).order_by(Tienda.nombre)).all()
        if tipo:
            tiendas = [t for t in tiendas if t.tipo == tipo]
        lugares = [h.lugar_dict(t) for t in tiendas]
        return [l for l in lugares if l["abierto_ahora"] is not False] if solo_abiertos else lugares
    return h.buscar_lugares(db, palabras_clave=[q], tipo=tipo, solo_abiertos=solo_abiertos)["resultados"]


@router.get("/lugares/{lugar_id}")
def detalle_lugar(lugar_id: int, db: Session = Depends(get_session)):
    tienda = db.get(Tienda, lugar_id)
    if not tienda:
        raise HTTPException(status_code=404, detail="Lugar no encontrado")
    hoy = h.ahora().date()
    productos = db.exec(select(Producto).where(Producto.tienda_id == lugar_id)).all()
    promociones = db.exec(
        select(Promocion).where(
            Promocion.tienda_id == lugar_id, Promocion.fecha_inicio <= hoy, Promocion.fecha_fin >= hoy
        )
    ).all()
    return {
        **h.lugar_dict(tienda),
        "productos": [h.producto_dict(p, tienda) for p in productos],
        "promociones": [h.promocion_dict(pr, tienda) for pr in promociones],
    }


@router.get("/productos")
def listar_productos(q: str = "", precio_max: float = 0, db: Session = Depends(get_session)):
    return h.buscar_productos(db, palabras_clave=[q] if q else None, precio_maximo=precio_max)["resultados"]


@router.get("/promociones")
def listar_promociones(q: str = "", db: Session = Depends(get_session)):
    return h.ver_promociones(db, palabras_clave=[q] if q else None)["resultados"]


@router.get("/eventos")
def listar_eventos(desde: str = "", dias: int = 30, db: Session = Depends(get_session)):
    return h.ver_eventos(db, desde=desde, dias=dias)["resultados"]


@router.get("/faqs")
def listar_faqs(q: Optional[str] = None, db: Session = Depends(get_session)):
    if q:
        return h.info_general(db, tema=q)["resultados"]
    return db.exec(select(Faq)).all()
