"""Paseo Points: lectura de la base MySQL del programa de fidelización (otro equipo, Prisma).

Solo consulta: compras, canjes y movimientos los registra la plataforma de Paseo Points.
Prisma guarda las fechas en UTC; aquí se devuelven en hora de Bolivia.
"""

import logging
import re
import threading
import time
from datetime import timezone
from typing import Callable
from urllib.parse import unquote, urlparse

import pymysql

from .config import PUNTOS_DATABASE_URL, PUNTOS_DB_CA, PUNTOS_TIMEOUT_S, ZONA_HORARIA

log = logging.getLogger("jarvis")

CACHE_S = 300
INTENTOS = 3
CONEXION_S = 3
LIMITE_TARJETAS = 6
NO_DISPONIBLE = "Paseo Points no responde en este momento."
TEMAS = ["todo", "recompensas", "niveles", "promociones", "misiones", "eventos"]

_cache: dict[str, tuple[float, dict]] = {}
# Una sola conexión reutilizada: abrir una nueva hacia Aiven cuesta 1-4 s y a veces se pierde.
_con = None
_candado = threading.Lock()


def configurado() -> bool:
    return bool(PUNTOS_DATABASE_URL)


def _conectar():
    url = urlparse(PUNTOS_DATABASE_URL)
    return pymysql.connect(
        host=url.hostname, port=url.port or 3306, database=url.path.lstrip("/"),
        user=unquote(url.username or ""), password=unquote(url.password or ""),
        ssl={"ca": str(PUNTOS_DB_CA)} if PUNTOS_DB_CA else None,
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
    return fecha.replace(tzinfo=timezone.utc).astimezone(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M")


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
        "nivel_estatus": r["nivel_estatus"] or 0, "nombre": r["negocio"],
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
    """Datos públicos del programa, en caché unos minutos; si la base falla se usa la última copia."""
    guardado = _cache.get("programa")
    if guardado and time.monotonic() - guardado[0] < CACHE_S:
        return guardado[1]
    try:
        datos = _consultar(_leer_programa)
    except pymysql.MySQLError:
        if guardado:
            log.warning("Paseo Points no respondió; uso datos en caché", exc_info=True)
            return guardado[1]
        raise
    _cache["programa"] = (time.monotonic(), datos)
    return datos


def _refrescar_siempre() -> None:
    while True:
        try:
            _cache["programa"] = (time.monotonic(), _consultar(_leer_programa))
        except Exception:
            log.warning("No se pudo refrescar Paseo Points", exc_info=True)
        time.sleep(CACHE_S - 30)


def iniciar() -> None:
    """Carga el programa en segundo plano al arrancar y lo mantiene fresco, para no demorar al chat."""
    if configurado():
        threading.Thread(target=_refrescar_siempre, name="paseo-points", daemon=True).start()


def estado() -> str:
    if not configurado():
        return "apagado"
    guardado = _cache.get("programa")
    if not guardado:
        return "conectando"
    return f"ok (datos de hace {int(time.monotonic() - guardado[0])} s)"


def _publico(item: dict) -> dict:
    return {k: v for k, v in item.items() if k != "nivel_estatus"}


# ---------- Herramientas (firma (db, ...) como el resto; db es la base local y no se usa) ----------

def programa_puntos(db, tema: str = "todo") -> dict:
    if not configurado():
        return {"error": "Paseo Points no está conectado.", "resultados": []}
    try:
        datos = _programa()
    except pymysql.MySQLError:
        log.exception("Error leyendo Paseo Points")
        return {"error": NO_DISPONIBLE, "resultados": []}

    tema = tema if tema in TEMAS else "todo"
    respuesta = {"como_funciona": datos["como_funciona"], "comercios_participantes": datos["comercios_participantes"]}
    for clave in TEMAS[1:]:
        if tema in ("todo", clave):
            respuesta[clave] = [_publico(x) for x in datos[clave]]
    tarjetas = datos["recompensas"] if tema == "todo" else datos[tema]
    respuesta["resultados"] = [_publico(x) for x in tarjetas[:LIMITE_TARJETAS]]
    return respuesta


def mis_puntos(db, celular: str = "", correo: str = "") -> dict:
    if not configurado():
        return {"error": "Paseo Points no está conectado.", "resultados": []}
    digitos = re.sub(r"\D", "", celular or "")[-8:]
    correo = (correo or "").strip().lower()
    if len(digitos) < 7 and "@" not in correo:
        return {"error": "Falta el celular o el correo con el que la persona se registró en Paseo Points.",
                "resultados": []}

    def leer(c):
        c.execute("""SELECT id, firstName, phone, email FROM User
                     WHERE role = 'CUSTOMER' AND status = 'ACTIVE' AND deletedAt IS NULL
                       AND ((%s <> '' AND LOWER(email) = %s) OR (%s <> '' AND phone LIKE %s))""",
                  (correo, correo, digitos, f"%{digitos}"))
        candidatos = [u for u in c.fetchall()
                      if (correo and (u["email"] or "").lower() == correo)
                      or (digitos and re.sub(r"\D", "", u["phone"] or "").endswith(digitos))]
        if len(candidatos) != 1:
            return {"encontrados": len(candidatos)}
        u = candidatos[0]
        c.execute("SELECT COALESCE(SUM(amount), 0) AS n FROM PointMovement WHERE userId = %s", (u["id"],))
        saldo = int(c.fetchone()["n"])
        c.execute("SELECT COALESCE(SUM(amount), 0) AS n FROM StatusMovement WHERE userId = %s", (u["id"],))
        estatus = int(c.fetchone()["n"])
        c.execute(f"""SELECT m.name, m.goal, m.rewardPoints, mp.progress FROM MissionProgress mp
                      JOIN Mission m ON m.id = mp.missionId
                      WHERE mp.userId = %s AND mp.completedAt IS NULL AND {_vigente('m')}""", (u["id"],))
        misiones = [{"nombre": m["name"], "avance": f"{m['progress']} de {m['goal']}", "puntos": m["rewardPoints"]}
                    for m in c.fetchall()]
        c.execute("SELECT COUNT(*) AS n FROM Redemption WHERE userId = %s AND status = 'PENDING'", (u["id"],))
        return {"encontrados": 1, "nombre": u["firstName"], "saldo": saldo, "estatus": estatus,
                "misiones": misiones, "canjes_pendientes": c.fetchone()["n"]}

    try:
        cliente = _consultar(leer)
        datos = _programa()
    except pymysql.MySQLError:
        log.exception("Error leyendo Paseo Points")
        return {"error": NO_DISPONIBLE, "resultados": []}

    if cliente["encontrados"] == 0:
        return {"error": "No hay una cuenta de Paseo Points con ese dato.", "resultados": []}
    if cliente["encontrados"] > 1:
        return {"error": "Ese dato coincide con varias cuentas; pide el correo registrado.", "resultados": []}

    saldo, estatus = cliente["saldo"], cliente["estatus"]
    niveles = datos["niveles"]
    actual = max((n for n in niveles if n["estatus_minimo"] <= estatus), key=lambda n: n["estatus_minimo"],
                 default=niveles[0] if niveles else None)
    siguiente = min((n for n in niveles if n["estatus_minimo"] > estatus), key=lambda n: n["estatus_minimo"],
                    default=None)
    permitidas = [r for r in datos["recompensas"] if r["nivel_estatus"] <= estatus]
    alcanzables = [r for r in permitidas if r["costo_puntos"] <= saldo]
    proxima = next((r for r in permitidas if r["costo_puntos"] > saldo), None)

    nivel = actual["nombre"] if actual else None
    return {
        "cliente": cliente["nombre"],
        "saldo_puntos": saldo,
        "nivel": nivel,
        "estatus": estatus,
        "siguiente_nivel": siguiente and {"nombre": siguiente["nombre"],
                                          "faltan_estatus": siguiente["estatus_minimo"] - estatus},
        "recompensas_alcanzables": [_publico(r) for r in alcanzables],
        "proxima_recompensa": proxima and {**_publico(proxima), "faltan_puntos": proxima["costo_puntos"] - saldo},
        "misiones_en_curso": cliente["misiones"],
        "canjes_pendientes": cliente["canjes_pendientes"],
        "resultados": [{"id": "mis-puntos", "tipo": "puntos", "nombre": cliente["nombre"], "saldo": saldo,
                        "nivel": nivel}] + [_publico(r) for r in alcanzables[:LIMITE_TARJETAS - 1]],
    }
