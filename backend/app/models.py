from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from .config import ZONA_HORARIA


class TiendaBase(SQLModel):
    nombre: str = Field(index=True)
    tipo: str = "tienda"  # tienda | restaurante | oficina | servicio
    categoria: str
    descripcion: str = ""
    piso: str
    sector: str = ""
    local: str = ""
    referencia: str = ""
    telefono: str = ""
    whatsapp: str = ""
    instagram: str = ""
    facebook: str = ""
    logo_url: str = ""
    hora_apertura: str = "10:00"  # HH:MM
    hora_cierre: str = "22:00"
    apertura_domingo: str = ""  # vacío en ambos = cerrado los domingos
    cierre_domingo: str = ""
    horario_confirmado: bool = False
    etiquetas: str = ""  # palabras clave separadas por coma
    mapa_x: Optional[float] = None  # posición 0-100 en el plano del Paseo
    mapa_y: Optional[float] = None


class Tienda(TiendaBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class ProductoBase(SQLModel):
    tienda_id: int = Field(foreign_key="tienda.id", index=True)
    nombre: str
    descripcion: str = ""
    precio: float
    stock: int = 0
    etiquetas: str = ""


class Producto(ProductoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class PromocionBase(SQLModel):
    tienda_id: Optional[int] = Field(default=None, foreign_key="tienda.id")
    titulo: str
    descripcion: str = ""
    fecha_inicio: date
    fecha_fin: date


class Promocion(PromocionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class EventoBase(SQLModel):
    nombre: str
    descripcion: str = ""
    fecha: date
    hora_inicio: str = ""
    hora_fin: str = ""
    lugar: str = ""


class Evento(EventoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class FaqBase(SQLModel):
    pregunta: str
    respuesta: str
    etiquetas: str = ""


class Faq(FaqBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class Consulta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    texto: str
    respuesta: str = ""
    herramientas: str = "[]"  # JSON: [{nombre, argumentos, resultados}]
    sin_resultados: bool = False
    duracion_ms: int = 0
    creado: datetime = Field(default_factory=lambda: datetime.now(ZONA_HORARIA), index=True)
