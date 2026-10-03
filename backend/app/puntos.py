"""Paseo Points: lectura de la base MySQL del programa de fidelización (otro equipo, Prisma).

Solo consulta: compras, canjes y movimientos los registra la plataforma de Paseo Points.
Prisma guarda las fechas en UTC; aquí se devuelven en hora de Bolivia.
"""

import logging
import copy
import json
import os
from pathlib import Path
import re
import threading
import time
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import unquote, urlparse

import pymysql

from .config import PUNTOS_DATABASE_URL, PUNTOS_DB_CA, PUNTOS_TIMEOUT_S, ZONA_HORARIA

log = logging.getLogger("jarvis")

CACHE_S = 300
MAX_STALE_S = 600
INTENTOS = 1
CONEXION_S = 3
LIMITE_TARJETAS = 6
NO_DISPONIBLE = "Paseo Points no responde en este momento."
TEMAS = ["todo", "recompensas", "niveles", "promociones", "misiones", "eventos"]

_cache: dict[str, tuple[float, dict]] = {}
# Una sola conexión reutilizada: abrir una nueva hacia Aiven cuesta 1-4 s y a veces se pierde.
_con = None
_candado = threading.Lock()


def configurado() -> bool:
    return bool(PUNTOS_DATABASE_URL and PUNTOS_DB_CA and PUNTOS_DB_CA.is_file())


def _conectar():
    url = urlparse(PUNTOS_DATABASE_URL)
    return pymysql.connect(
        host=url.hostname, port=url.port or 3306, database=url.path.lstrip("/"),
        user=unquote(url.username or ""), password=unquote(url.password or ""),
        ssl={"ca": str(PUNTOS_DB_CA)}, ssl_verify_cert=True, ssl_verify_identity=True,
        connect_timeout=CONEXION_S, read_timeout=PUNTOS_TIMEOUT_S, write_timeout=PUNTOS_TIMEOUT_S,
        # autocommit: sin él, la conexión reutilizada vería siempre la misma foto de los datos
        autocommit=True, init_command="SET SESSION TRANSACTION READ ONLY",
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
    )


def _consultar(funcion: Callable):
    """Ejecuta funcion(cursor) sobre la conexión compartida; si se cayó, reconecta y reintenta."""
    global _con
    with _candado:
        for intento in range(INTENTOS):
            try:
                if _con is None:
                    _con = _conectar()
                else:
                    _con.ping(reconnect=True)
                with _con.cursor() as c:
                    return funcion(c)
            except pymysql.err.OperationalError:
                try:
                    if _con is not None:
                        _con.close()
                except Exception:
                    pass
                _con = None
                if intento == INTENTOS - 1:
                    raise
                log.warning("Paseo Points no respondió (intento %s); reintentando", intento + 1)


def _vigente(alias: str) -> str:
    return (f"{alias}.status = 'ACTIVE' AND {alias}.deletedAt IS NULL "
            f"AND ({alias}.startsAt IS NULL OR {alias}.startsAt <= UTC_TIMESTAMP(3)) "
            f"AND ({alias}.endsAt IS NULL OR {alias}.endsAt >= UTC_TIMESTAMP(3))")


def _local(fecha) -> str | None:
    if fecha is None:
        return None
    return fecha.replace(tzinfo=timezone.utc).astimezone(ZONA_HORARIA).isoformat(timespec="minutes")


def _num(valor) -> str:
    return f"{float(valor):g}"


def _beneficio(r: dict) -> str:
    if r["type"] == "AMOUNT_DISCOUNT":
        texto = f"Descuento de Bs {_num(r['discountAmount'])}"
    elif r["type"] == "PERCENT_DISCOUNT":
        texto = f"{r['discountPercent']}% de descuento"
    else:
        cantidad = f"{r['quantity']} " if (r["quantity"] or 1) > 1 else ""
        texto = f"{cantidad}{r['producto'] or 'Producto'} gratis"
    if r["minimumPurchase"]:
        texto += f" en compras desde Bs {_num(r['minimumPurchase'])}"
    return texto


def _leer_programa(c) -> dict:
    c.execute("SELECT value FROM SystemSetting WHERE `key` = 'POINTS_BASE_RATE'")
    fila = c.fetchone()
    tasa = float(fila["value"]) if fila else 1.0

    c.execute("SELECT id, name, minimumStatus, pointsMultiplier FROM Tier WHERE isActive = 1 ORDER BY sortOrder")
    niveles = [{"id": f"nivel-{t['id']}", "tipo": "nivel", "nombre": t["name"], "estatus_minimo": t["minimumStatus"],
                "multiplicador": float(t["pointsMultiplier"])} for t in c.fetchall()]

    c.execute(f"""
        SELECT r.*, b.name AS negocio, b.floor, b.localNumber, b.sector, ci.name AS producto,
               t.name AS nivel, t.minimumStatus AS nivel_estatus
        FROM Reward r
        LEFT JOIN Business b ON b.id = r.businessId
        LEFT JOIN CatalogItem ci ON ci.id = r.catalogItemId
        LEFT JOIN Tier t ON t.id = r.minimumTierId
        WHERE {_vigente('r')} AND (r.stock IS NULL OR r.stock > 0)
        ORDER BY r.pointsCost""")
    recompensas = [{
        "id": f"recompensa-{r['id']}", "tipo": "recompensa", "titulo": _beneficio(r),
        "detalle": r["description"], "costo_puntos": r["pointsCost"], "nivel_minimo": r["nivel"],
        "nivel_estatus": r["nivel_estatus"] or 0, "nombre": r["negocio"], "vigente_hasta": _local(r["endsAt"]),
        "ubicacion": {"piso": r["floor"], "local": r["localNumber"], "sector": r["sector"]},
    } for r in c.fetchall()]

    c.execute(f"""
        SELECT p.id, p.name, p.type, p.value, p.endsAt,
               (SELECT GROUP_CONCAT(b.name SEPARATOR ', ') FROM PromotionBusiness pb
                JOIN Business b ON b.id = pb.businessId WHERE pb.promotionId = p.id) AS negocios,
               (SELECT GROUP_CONCAT(cat.name SEPARATOR ', ') FROM PromotionCategory pc
                JOIN Category cat ON cat.id = pc.categoryId WHERE pc.promotionId = p.id) AS categorias
        FROM Promotion p WHERE {_vigente('p')} ORDER BY p.endsAt""")
    promociones = []
    for p in c.fetchall():
        beneficio = f"Puntos x{_num(p['value'])}" if p["type"] == "POINTS_MULTIPLIER" else f"+{_num(p['value'])} puntos"
        donde = ", ".join(x for x in (p["negocios"], p["categorias"]) if x)
        promociones.append({"id": f"promo-puntos-{p['id']}", "tipo": "promocion", "titulo": p["name"],
                            "descripcion": f"{beneficio}{' en ' + donde if donde else ''}",
                            "vigente_hasta": _local(p["endsAt"])})

    c.execute(f"SELECT id, name, description, goal, rewardPoints, endsAt FROM Mission m WHERE {_vigente('m')} ORDER BY rewardPoints")
    misiones = [{"id": f"mision-{m['id']}", "tipo": "mision", "nombre": m["name"], "descripcion": m["description"],
                 "meta": m["goal"], "puntos": m["rewardPoints"], "vigente_hasta": _local(m["endsAt"])}
                for m in c.fetchall()]

    c.execute("""SELECT id, name, description, location, startsAt, endsAt, pointsReward FROM Event
                 WHERE status = 'ACTIVE' AND deletedAt IS NULL AND endsAt >= UTC_TIMESTAMP(3)
                 ORDER BY startsAt LIMIT 5""")
    eventos = []
    for e in c.fetchall():
        inicio = _local(e["startsAt"]) or ""
        eventos.append({"id": f"evento-puntos-{e['id']}", "tipo": "evento", "nombre": e["name"],
                        "descripcion": e["description"], "lugar": e["location"], "fecha": inicio[:10],
                        "hora_inicio": inicio[11:], "termina": _local(e["endsAt"]), "puntos": e["pointsReward"]})

    c.execute("SELECT COUNT(*) AS n FROM Business WHERE status = 'ACTIVE' AND deletedAt IS NULL")
    return {
        "como_funciona": (f"Por cada Bs 1 de compra en comercios participantes se gana {_num(tasa)} punto(s), "
                          "multiplicado según el nivel. El nivel sube con el estatus acumulado por compras y misiones. "
                          "Los puntos se canjean por recompensas en la app de Paseo Points o en el local."),
        "comercios_participantes": c.fetchone()["n"],
        "niveles": niveles, "recompensas": recompensas, "promociones": promociones,
        "misiones": misiones, "eventos": eventos,
    }


def _programa() -> dict:
    """Chat never waits on MySQL; background refresh supplies a bounded public snapshot."""
    saved = _cache.get("programa")
    if not saved or time.monotonic() - saved[0] > MAX_STALE_S:
        raise RuntimeError(NO_DISPONIBLE)
    age = int(time.monotonic() - saved[0])
    data = copy.deepcopy(saved[1])
    now = datetime.now(timezone.utc)
    _filter_expired(data, now)
    data["freshness"] = {"age_seconds": age, "stale": age >= CACHE_S, "max_age_seconds": MAX_STALE_S, 'source':'points_mysql'}
    return data


def _filter_expired(data, now):
    for key in ("recompensas", "promociones", "misiones", "eventos"):
        data[key] = [item for item in data[key] if not (item.get("vigente_hasta") or item.get("termina")) or
                     datetime.fromisoformat(item.get("vigente_hasta") or item["termina"]).astimezone(timezone.utc) > now]


def _demo_programa():
    if os.getenv('JARVIS_DEMO_CATALOG') != '1':
        raise RuntimeError('Paseo Points no está conectado.')
    data = json.loads((Path(__file__).parent/'datos'/'points-demo.json').read_text(encoding='utf-8'))
    _filter_expired(data, datetime.now(timezone.utc))
    data['freshness'] = {'age_seconds':0,'stale':False,'source':'synthetic_demo','external_connected':False}
    for key in TEMAS[1:]:
        for item in data[key]:
            item.update(demo=True,fuente_url='/catalog/demo')
    return data


def _refrescar_siempre() -> None:
    while True:
        try:
            _cache["programa"] = (time.monotonic(), _consultar(_leer_programa))
        except Exception as exc:
            log.warning("No se pudo refrescar Paseo Points (%s)", type(exc).__name__)
        time.sleep(CACHE_S - 30)


def iniciar() -> None:
    """Carga el programa en segundo plano al arrancar y lo mantiene fresco, para no demorar al chat."""
    if configurado():
        threading.Thread(target=_refrescar_siempre, name="paseo-points", daemon=True).start()


def estado() -> str:
    if not configurado():
        return "demo público (sin conexión real)" if os.getenv('JARVIS_DEMO_CATALOG')=='1' else "apagado (URL y CA TLS requeridos)"
    guardado = _cache.get("programa")
    if not guardado:
        return "conectando"
    age = int(time.monotonic() - guardado[0])
    return f"{'ok' if age < CACHE_S else 'stale' if age <= MAX_STALE_S else 'no disponible'} (datos de hace {age} s)"


def _publico(item: dict) -> dict:
    return {k: v for k, v in item.items() if k != "nivel_estatus"}


# ---------- Herramientas (firma (db, ...) como el resto; db es la base local y no se usa) ----------

def programa_puntos(db, tema: str = "todo") -> dict:
    try:
        datos = _programa() if configurado() else _demo_programa()
    except (pymysql.MySQLError, RuntimeError):
        log.warning("Programa público de Points no disponible")
        try:
            datos = _demo_programa()
        except RuntimeError:
            return {"error": NO_DISPONIBLE, "resultados": []}

    tema = tema if tema in TEMAS else "todo"
    respuesta = {"como_funciona": datos["como_funciona"], "comercios_participantes": datos["comercios_participantes"], "freshness": datos["freshness"]}
    for clave in TEMAS[1:]:
        if tema in ("todo", clave):
            respuesta[clave] = [_publico(x) for x in datos[clave]]
    tarjetas = datos["recompensas"] if tema == "todo" else datos[tema]
    respuesta["resultados"] = [_publico(x) for x in tarjetas[:LIMITE_TARJETAS]]
    return respuesta


def mis_puntos(db, celular: str = "", correo: str = "") -> dict:
    """Disabled: personal data requires a verified external identity, not an identifier."""
    return {"error": "Inicia sesión en Paseo Points para consultar tu saldo. La consulta personal aquí está deshabilitada hasta verificar identidad.", "resultados": []}
