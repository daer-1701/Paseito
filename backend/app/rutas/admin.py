from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session, SQLModel, select

from ..config import ADMIN_TOKEN
from ..db import get_session
from ..models import (
    Evento, EventoBase, Faq, FaqBase, Producto, ProductoBase, Promocion, PromocionBase,
    Tienda, TiendaBase,
)


def verificar_admin(x_admin_token: str = Header(default="")):
    if ADMIN_TOKEN and x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Token de administrador inválido")


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(verificar_admin)])


def registrar_crud(ruta: str, tabla: type[SQLModel], base: type[SQLModel]) -> None:
    @router.get(f"/{ruta}", response_model=list[tabla], name=f"listar_{ruta}")
    def listar(db: Session = Depends(get_session)):
        return db.exec(select(tabla)).all()

    @router.get(f"/{ruta}/{{item_id}}", response_model=tabla, name=f"obtener_{ruta}")
    def obtener(item_id: int, db: Session = Depends(get_session)):
        item = db.get(tabla, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="No encontrado")
        return item

    @router.post(f"/{ruta}", response_model=tabla, status_code=201, name=f"crear_{ruta}")
    def crear(datos: base, db: Session = Depends(get_session)):
        item = tabla.model_validate(datos)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @router.put(f"/{ruta}/{{item_id}}", response_model=tabla, name=f"actualizar_{ruta}")
    def actualizar(item_id: int, datos: base, db: Session = Depends(get_session)):
        item = db.get(tabla, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="No encontrado")
        item.sqlmodel_update(datos.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @router.delete(f"/{ruta}/{{item_id}}", status_code=204, name=f"eliminar_{ruta}")
    def eliminar(item_id: int, db: Session = Depends(get_session)):
        item = db.get(tabla, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="No encontrado")
        db.delete(item)
        db.commit()


registrar_crud("lugares", Tienda, TiendaBase)
registrar_crud("productos", Producto, ProductoBase)
registrar_crud("promociones", Promocion, PromocionBase)
registrar_crud("eventos", Evento, EventoBase)
registrar_crud("faqs", Faq, FaqBase)
