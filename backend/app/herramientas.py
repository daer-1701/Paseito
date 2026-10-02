"""Herramientas que el agente puede invocar. Toda cifra o dato que Paseito menciona sale de aquí."""

import difflib
import unicodedata
from datetime import date, datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from .config import ZONA_HORARIA
from .models import Evento, Faq, Producto, Promocion, Tienda

LIMITE_LUGARES = 6
LIMITE_PRODUCTOS = 8
LIMITE_PROMOCIONES = 6
LIMITE_FAQS = 3

STOPWORDS = {
    "de", "del", "la", "el", "los", "las", "un", "una", "unos", "unas", "para", "con",
    "por", "en", "y", "o", "que", "algo", "donde", "quiero", "busco", "necesito",
}


# ---------- Utilidades ----------

def ahora() -> datetime:
    return datetime.now(ZONA_HORARIA)


def normalizar(texto: Optional[str]) -> str:
    texto = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def _tokens(palabras: Optional[list]) -> list[str]:
    tokens: list[str] = []
    for frase in palabras or []:
        for tok in normalizar(str(frase)).replace(",", " ").split():
            if len(tok) >= 3 and tok not in STOPWORDS and tok not in tokens:
                tokens.append(tok)
    return tokens


def _variantes(tok: str) -> set[str]:
    variantes = {tok}
    if len(tok) > 5 and tok.endswith("es"):
        variantes.add(tok[:-2])
    if len(tok) > 4 and tok.endswith("s"):
        variantes.add(tok[:-1])
    if len(tok) >= 6:
        variantes.add(tok[: max(5, len(tok) - 3)])  # raíz: "estaciono" -> "estaci"
    return variantes


def _puntaje(campos: list[tuple[str, int]], tokens: list[str]) -> int:
    """Suma, por cada token, el mayor peso entre los campos donde aparece."""
    campos_norm = [(normalizar(texto), peso) for texto, peso in campos]
    total = 0
    for tok in tokens:
        variantes = _variantes(tok)
        total += max(
            (peso for texto, peso in campos_norm if any(v in texto for v in variantes)),
            default=0,
        )
    return total


def _a_minutos(hora: str) -> int:
    hh, mm = hora.strip().split(":")
    return int(hh) * 60 + int(mm)


def esta_abierto(tienda: Tienda, momento: Optional[datetime] = None) -> Optional[bool]:
    momento = momento or ahora()
    actual = momento.hour * 60 + momento.minute
    apertura, cierre = tienda.hora_apertura, tienda.hora_cierre
    if momento.weekday() == 6:
        if not (tienda.apertura_domingo and tienda.cierre_domingo):
            return False if apertura else None
        apertura, cierre = tienda.apertura_domingo, tienda.cierre_domingo
    try:
        apertura, cierre = _a_minutos(apertura), _a_minutos(cierre)
    except (ValueError, AttributeError):
        return None
    if apertura < cierre:
        return apertura <= actual < cierre
    return actual >= apertura or actual < cierre


def _parse_fecha(valor: str) -> Optional[date]:
    try:
        return date.fromisoformat(valor.strip())
    except (ValueError, AttributeError):
        return None


# ---------- Serializadores ----------

def lugar_dict(t: Tienda) -> dict:
    return {
        "id": t.id,
        "nombre": t.nombre,
        "tipo": t.tipo,
        "categoria": t.categoria,
        "descripcion": t.descripcion,
        "ubicacion": {
            "piso": t.piso,
            "sector": t.sector,
            "local": t.local,
            "referencia": t.referencia,
            "mapa_x": t.mapa_x,
            "mapa_y": t.mapa_y,
        },
        "horario": _texto_horario(t),
        "horario_confirmado": t.horario_confirmado,
        "abierto_ahora": esta_abierto(t),
        "telefono": t.telefono,
        "whatsapp": t.whatsapp,
        "instagram": t.instagram,
        "logo_url": t.logo_url,
    }


def _texto_horario(t: Tienda) -> str:
    if not t.hora_apertura:
        return "sin información de horario"
    semana = f"lunes a sábado {t.hora_apertura} a {t.hora_cierre}"
    if t.apertura_domingo and t.cierre_domingo:
        return f"{semana}; domingo {t.apertura_domingo} a {t.cierre_domingo}"
    return f"{semana}; domingo cerrado"


def producto_dict(p: Producto, t: Optional[Tienda]) -> dict:
    return {
        "id": p.id,
        "nombre": p.nombre,
        "descripcion": p.descripcion,
        "precio_bs": p.precio,
        "disponible": p.stock > 0,
        "stock": p.stock,
        "tienda": None if t is None else {
            "id": t.id, "nombre": t.nombre, "piso": t.piso, "local": t.local, "sector": t.sector,
        },
    }


def promocion_dict(pr: Promocion, t: Optional[Tienda]) -> dict:
    return {
        "id": pr.id,
        "titulo": pr.titulo,
        "descripcion": pr.descripcion,
        "vigente_hasta": pr.fecha_fin.isoformat(),
        "tienda": None if t is None else {
            "id": t.id, "nombre": t.nombre, "piso": t.piso, "local": t.local,
        },
    }


def evento_dict(e: Evento) -> dict:
    return {
        "id": e.id,
        "nombre": e.nombre,
        "descripcion": e.descripcion,
        "fecha": e.fecha.isoformat(),
        "hora_inicio": e.hora_inicio,
        "hora_fin": e.hora_fin,
        "lugar": e.lugar,
    }


# ---------- Herramientas ----------

def buscar_lugares(db: Session, palabras_clave: Optional[list] = None, tipo: str = "",
                   solo_abiertos: bool = False) -> dict:
    tokens = _tokens(palabras_clave)
    tiendas = db.exec(select(Tienda)).all()
    if tipo:
        tiendas = [t for t in tiendas if normalizar(t.tipo) == normalizar(tipo)]

    productos_por_tienda: dict[int, str] = {}
    if tokens:
        for p in db.exec(select(Producto)).all():
            productos_por_tienda[p.tienda_id] = (
                productos_por_tienda.get(p.tienda_id, "") + f" {p.nombre} {p.etiquetas}"
            )

    puntuadas = []
    for t in tiendas:
        if solo_abiertos and esta_abierto(t) is False:
            continue
        puntaje = _puntaje(
            [(t.nombre, 3), (t.categoria, 2), (t.etiquetas, 2), (t.descripcion, 1),
             (productos_por_tienda.get(t.id, ""), 1)],
            tokens,
        ) if tokens else 1
        if puntaje > 0:
            puntuadas.append((puntaje, t))

    puntuadas.sort(key=lambda x: -x[0])
    return {
        "resultados": [lugar_dict(t) for _, t in puntuadas[:LIMITE_LUGARES]],
        "total_encontrados": len(puntuadas),
    }


def buscar_productos(db: Session, palabras_clave: Optional[list] = None,
                     precio_maximo: float = 0) -> dict:
    tokens = _tokens(palabras_clave)
    tiendas = {t.id: t for t in db.exec(select(Tienda)).all()}

    puntuados = []
    for p in db.exec(select(Producto)).all():
        if precio_maximo and p.precio > precio_maximo:
            continue
        t = tiendas.get(p.tienda_id)
        puntaje = _puntaje(
            [(p.nombre, 3), (p.etiquetas, 2), (p.descripcion, 1),
             (t.categoria if t else "", 1)],
            tokens,
        ) if tokens else 1
        if puntaje > 0:
            puntuados.append((puntaje, p, t))

    puntuados.sort(key=lambda x: (-x[0], not x[1].stock > 0, x[1].precio))
    return {
        "resultados": [producto_dict(p, t) for _, p, t in puntuados[:LIMITE_PRODUCTOS]],
        "total_encontrados": len(puntuados),
    }


def ver_promociones(db: Session, palabras_clave: Optional[list] = None) -> dict:
    hoy = ahora().date()
    tokens = _tokens(palabras_clave)
    tiendas = {t.id: t for t in db.exec(select(Tienda)).all()}

    vigentes = db.exec(
        select(Promocion).where(Promocion.fecha_inicio <= hoy, Promocion.fecha_fin >= hoy)
    ).all()

    puntuadas = []
    for pr in vigentes:
        t = tiendas.get(pr.tienda_id) if pr.tienda_id else None
        puntaje = _puntaje(
            [(pr.titulo, 3), (pr.descripcion, 1),
             (t.nombre if t else "", 3), (t.categoria if t else "", 2)],
            tokens,
        ) if tokens else 1
        if puntaje > 0:
            puntuadas.append((puntaje, pr, t))

    puntuadas.sort(key=lambda x: (-x[0], x[1].fecha_fin))
    return {
        "resultados": [promocion_dict(pr, t) for _, pr, t in puntuadas[:LIMITE_PROMOCIONES]],
        "total_encontrados": len(puntuadas),
    }


def ver_eventos(db: Session, desde: str = "", dias: int = 7) -> dict:
    inicio = _parse_fecha(desde) or ahora().date()
    fin = inicio + timedelta(days=max(0, int(dias)))
    eventos = db.exec(
        select(Evento)
        .where(Evento.fecha >= inicio, Evento.fecha <= fin)
        .order_by(Evento.fecha, Evento.hora_inicio)
    ).all()
    return {"resultados": [evento_dict(e) for e in eventos], "total_encontrados": len(eventos)}


def ubicar_lugar(db: Session, nombre: str) -> dict:
    buscado = normalizar(nombre)
    candidatos = []
    for t in db.exec(select(Tienda)).all():
        actual = normalizar(t.nombre)
        similitud = difflib.SequenceMatcher(None, buscado, actual).ratio()
        if buscado and (buscado in actual or actual in buscado):
            similitud = max(similitud, 0.9)
        if similitud >= 0.6:
            candidatos.append((similitud, t))

    candidatos.sort(key=lambda x: -x[0])
    if not candidatos:
        return buscar_lugares(db, palabras_clave=[nombre])
    if candidatos[0][0] >= 0.85:
        candidatos = [c for c in candidatos if c[0] >= 0.85]
    return {
        "resultados": [lugar_dict(t) for _, t in candidatos[:3]],
        "total_encontrados": len(candidatos),
    }


def info_general(db: Session, tema: str) -> dict:
    tokens = _tokens([tema])
    puntuadas = []
    for f in db.exec(select(Faq)).all():
        puntaje = _puntaje([(f.etiquetas, 3), (f.pregunta, 2), (f.respuesta, 1)], tokens)
        if puntaje > 0:
            puntuadas.append((puntaje, f))
    puntuadas.sort(key=lambda x: -x[0])
    return {
        "resultados": [
            {"id": f.id, "pregunta": f.pregunta, "respuesta": f.respuesta}
            for _, f in puntuadas[:LIMITE_FAQS]
        ],
        "total_encontrados": len(puntuadas),
    }


HERRAMIENTAS = {
    "buscar_lugares": buscar_lugares,
    "buscar_productos": buscar_productos,
    "ver_promociones": ver_promociones,
    "ver_eventos": ver_eventos,
    "ubicar_lugar": ubicar_lugar,
    "info_general": info_general,
}

TIPO_TARJETA = {
    "buscar_lugares": "lugar",
    "ubicar_lugar": "lugar",
    "buscar_productos": "producto",
    "ver_promociones": "promocion",
    "ver_eventos": "evento",
    "info_general": "info",
}


def ejecutar(nombre: str, argumentos: dict, db: Session) -> dict:
    funcion = HERRAMIENTAS.get(nombre)
    if funcion is None:
        return {"error": f"Herramienta desconocida: {nombre}"}
    try:
        return funcion(db, **argumentos)
    except TypeError as e:
        return {"error": f"Argumentos inválidos: {e}"}


_PALABRAS_CLAVE = {
    "type": "array",
    "items": {"type": "string"},
    "description": (
        "Palabras clave concretas derivadas de la intención del usuario, no la frase literal. "
        "Ej.: 'regalo para mi pareja' -> ['perfume', 'joyas', 'chocolates', 'flores']."
    ),
}

DECLARACIONES = [
    {
        "type": "function",
        "name": "buscar_lugares",
        "description": (
            "Busca tiendas, restaurantes, oficinas y servicios del Paseo Aranjuez. Devuelve "
            "ubicación (piso, sector, local, referencia), horario y si está abierto ahora."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "palabras_clave": _PALABRAS_CLAVE,
                "tipo": {
                    "type": "string",
                    "enum": ["tienda", "restaurante", "oficina", "servicio"],
                    "description": "Filtra por tipo de lugar (opcional).",
                },
                "solo_abiertos": {
                    "type": "boolean",
                    "description": "true para devolver solo lugares abiertos en este momento.",
                },
            },
        },
    },
    {
        "type": "function",
        "name": "buscar_productos",
        "description": (
            "Busca productos disponibles en las tiendas del Paseo con su precio en bolivianos, "
            "disponibilidad y la tienda donde se venden."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "palabras_clave": _PALABRAS_CLAVE,
                "precio_maximo": {
                    "type": "number",
                    "description": "Precio máximo en bolivianos (opcional).",
                },
            },
            "required": ["palabras_clave"],
        },
    },
    {
        "type": "function",
        "name": "ver_promociones",
        "description": "Lista las promociones y descuentos vigentes hoy en el Paseo.",
        "parameters": {
            "type": "object",
            "properties": {"palabras_clave": _PALABRAS_CLAVE},
        },
    },
    {
        "type": "function",
        "name": "ver_eventos",
        "description": "Lista los eventos y actividades programados en el Paseo.",
        "parameters": {
            "type": "object",
            "properties": {
                "desde": {
                    "type": "string",
                    "description": "Fecha inicial YYYY-MM-DD. Por defecto, hoy.",
                },
                "dias": {
                    "type": "integer",
                    "description": "Cantidad de días a cubrir desde la fecha inicial (0 = solo ese día).",
                },
            },
        },
    },
    {
        "type": "function",
        "name": "ubicar_lugar",
        "description": "Encuentra la ubicación exacta de un lugar del Paseo por su nombre.",
        "parameters": {
            "type": "object",
            "properties": {"nombre": {"type": "string", "description": "Nombre del lugar."}},
            "required": ["nombre"],
        },
    },
    {
        "type": "function",
        "name": "info_general",
        "description": (
            "Información general del Paseo: estacionamiento, horarios generales, baños, wifi, "
            "cajeros, seguridad, cómo llegar y otros servicios."
        ),
        "parameters": {
            "type": "object",
            "properties": {"tema": {"type": "string", "description": "Tema de la consulta."}},
            "required": ["tema"],
        },
    },
]
