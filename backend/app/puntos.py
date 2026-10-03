"""Paseo Points: lectura de la base MySQL del programa de fidelización (otro equipo, Prisma).

Solo consulta: compras, canjes y movimientos los registra la plataforma de Paseo Points.
Prisma guarda las fechas en UTC; aquí se devuelven en hora de Bolivia.
"""

import base64
import hashlib
import hmac
import json
import logging
import re
import threading
import time
from datetime import timezone
from typing import Callable
from urllib.parse import unquote, urlparse

import httpx
import pymysql

from .config import (PUNTOS_API_KEY, PUNTOS_API_URL, PUNTOS_DATABASE_URL, PUNTOS_DB_CA, PUNTOS_QR_SECRET,
                     PUNTOS_TIMEOUT_S, ZONA_HORARIA)

log = logging.getLogger("jarvis")

CACHE_S = 300
INTENTOS = 3
CONEXION_S = 3
LIMITE_TARJETAS = 6
NO_DISPONIBLE = "Paseo Points no responde en este momento."
TEMAS = ["todo", "recompensas", "niveles", "promociones", "misiones", "eventos"]
# Código de verificación de un canje (Redemption.verificationToken), p. ej. AB1C2-D3EF4.
CODIGO_CUPON = re.compile(r"\b[A-Z0-9]{5}-[A-Z0-9]{5}\b", re.IGNORECASE)
ESTADOS_CUPON = {"PENDING": "vigente", "REDEEMED": "canjeado", "EXPIRED": "vencido", "CANCELLED": "cancelado"}
LIMITE_OTROS_CUPONES = 5
# QR de cliente de la app: PP1.<datos>.<firma>, datos = base64url de {"u": id, "exp": ms} y
# firma = HMAC-SHA256 de <datos> en base64url. Vale entre 5 y 10 minutos; la app lo renueva sola.
QR_CLIENTE = re.compile(r"PP1\.([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)")
RUTA_VERIFICAR_QR = "/api/integrations/customer-qr/verify"
QR_NO_VALIDO = "No pude validar ese QR. Abre tu QR de cliente en la app de Paseo Points y muéstramelo de nuevo."
QR_VENCIDO = "Ese QR ya venció; la app lo renueva cada pocos minutos. Ábrelo de nuevo y muéstramelo."
CUENTA_NO_ENCONTRADA = "No encuentro esa cuenta en Paseo Points."
LIMITE_CUPONES_PASADOS = 3

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


def _nivel_actual(niveles: list[dict], estatus: int) -> dict | None:
    return max((n for n in niveles if n["estatus_minimo"] <= estatus), key=lambda n: n["estatus_minimo"],
               default=niveles[0] if niveles else None)


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
    actual = _nivel_actual(niveles, estatus)
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


# ---------- Cupones (canjes) leídos desde el QR que muestra la app ----------

_CONSULTA_CUPON = """
    SELECT r.id, r.status, r.pointsSpent, r.createdAt, r.redeemedAt, u.firstName,
           w.type, w.discountAmount, w.discountPercent, w.quantity, w.minimumPurchase, w.description,
           ci.name AS producto, b.name AS negocio, b.floor, b.localNumber, b.sector
    FROM Redemption r
    JOIN Reward w ON w.id = r.rewardId
    JOIN User u ON u.id = r.userId
    LEFT JOIN CatalogItem ci ON ci.id = w.catalogItemId
    LEFT JOIN Business b ON b.id = COALESCE(r.businessId, w.businessId)"""


def codigo_cupon(texto: str) -> str | None:
    """El QR puede traer solo el código o una URL/JSON que lo contiene."""
    hallado = CODIGO_CUPON.search(texto or "")
    return hallado.group(0).upper() if hallado else None


def _cupon(f: dict) -> dict:
    return {
        "id": f"cupon-{f['id']}", "tipo": "cupon", "titulo": _beneficio(f), "detalle": f["description"],
        "estado": ESTADOS_CUPON.get(f["status"], f["status"].lower()), "puntos_usados": f["pointsSpent"],
        "obtenido_el": _local(f["createdAt"]), "canjeado_el": _local(f["redeemedAt"]), "nombre": f["negocio"],
        "ubicacion": {"piso": f["floor"], "local": f["localNumber"], "sector": f["sector"]},
    }


def _b64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _verificar_qr_en_api(token: str) -> tuple[int | None, str | None]:
    """Pregunta a Paseo Points si el QR es auténtico; el secreto nunca sale de su servidor."""
    try:
        r = httpx.post(f"{PUNTOS_API_URL}{RUTA_VERIFICAR_QR}", json={"token": token},
                       headers={"x-api-key": PUNTOS_API_KEY}, timeout=PUNTOS_TIMEOUT_S)
    except httpx.HTTPError:
        log.warning("La API de Paseo Points no respondió al verificar un QR de cliente")
        return None, f"{NO_DISPONIBLE} Intenta de nuevo en un ratito."
    if r.status_code == 200:
        try:
            return int(r.json()["userId"]), None
        except (ValueError, KeyError, TypeError):
            log.error("Respuesta inesperada de Paseo Points al verificar un QR de cliente")
            return None, f"{NO_DISPONIBLE} Intenta de nuevo en un ratito."
    if r.status_code == 410:
        return None, QR_VENCIDO
    if r.status_code == 404:
        return None, CUENTA_NO_ENCONTRADA
    if r.status_code in (400, 401):
        # 401 es firma alterada o PUNTOS_API_KEY incorrecta; la API no los distingue
        log.warning("Paseo Points rechazó un QR de cliente (%s)", r.status_code)
        return None, QR_NO_VALIDO
    log.error("Paseo Points respondió %s al verificar un QR de cliente", r.status_code)
    return None, f"{NO_DISPONIBLE} Intenta de nuevo en un ratito."


def _verificar_qr_local(datos: str, firma: str) -> tuple[int | None, str | None]:
    """Respaldo sin API: valida la firma con un secreto dedicado al QR."""
    try:
        firma_recibida = _b64(firma)
        carga = json.loads(_b64(datos))
        usuario, vence_ms = int(carga["u"]), float(carga["exp"])
    except (ValueError, KeyError, TypeError):
        return None, QR_NO_VALIDO
    esperada = hmac.new(PUNTOS_QR_SECRET.encode(), datos.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(esperada, firma_recibida):
        log.warning("QR de cliente con firma inválida")
        return None, QR_NO_VALIDO
    if vence_ms / 1000 < time.time():
        return None, QR_VENCIDO
    return usuario, None


def cliente_del_qr(texto: str) -> tuple[int | None, str | None]:
    """(id del cliente, None) si es un QR de cliente auténtico y vigente; (None, motivo) si no vale;
    (None, None) si no es un QR de cliente. Sin validar la firma, cualquiera podría armar un QR con otro id."""
    hallado = QR_CLIENTE.search(texto or "")
    if not hallado:
        return None, None
    if PUNTOS_API_URL and PUNTOS_API_KEY:
        return _verificar_qr_en_api(hallado.group(0))
    if PUNTOS_QR_SECRET:
        return _verificar_qr_local(*hallado.groups())
    return None, "Este kiosco todavía no puede leer el QR de cliente. Muéstrame el QR de un cupón."


def cupones_del_cliente(usuario: int) -> dict:
    """Todos los cupones vigentes del cliente, los últimos usados o vencidos y su saldo de puntos."""
    def leer(c):
        c.execute("SELECT firstName FROM User WHERE id = %s AND status = 'ACTIVE' AND deletedAt IS NULL", (usuario,))
        cliente = c.fetchone()
        if not cliente:
            return None
        c.execute(f"{_CONSULTA_CUPON} WHERE r.userId = %s AND r.status = 'PENDING' ORDER BY r.createdAt DESC", (usuario,))
        vigentes = c.fetchall()
        c.execute(f"""{_CONSULTA_CUPON} WHERE r.userId = %s AND r.status <> 'PENDING'
                      ORDER BY COALESCE(r.redeemedAt, r.createdAt) DESC LIMIT %s""", (usuario, LIMITE_CUPONES_PASADOS))
        pasados = c.fetchall()
        c.execute("SELECT COALESCE(SUM(amount), 0) AS n FROM PointMovement WHERE userId = %s", (usuario,))
        saldo = int(c.fetchone()["n"])
        c.execute("SELECT COALESCE(SUM(amount), 0) AS n FROM StatusMovement WHERE userId = %s", (usuario,))
        return {"nombre": cliente["firstName"], "vigentes": vigentes, "pasados": pasados, "saldo": saldo,
                "estatus": int(c.fetchone()["n"])}

    try:
        datos = _consultar(leer)
        nivel = _nivel_actual(_programa()["niveles"], datos["estatus"]) if datos else None
    except pymysql.MySQLError:
        log.exception("Error leyendo los cupones de un cliente de Paseo Points")
        return {"error": f"{NO_DISPONIBLE} Intenta de nuevo en un ratito.", "resultados": []}
    if not datos:
        return {"error": CUENTA_NO_ENCONTRADA, "resultados": []}
    vigentes = [_cupon(f) for f in datos["vigentes"]]
    pasados = [_cupon(f) for f in datos["pasados"]]
    resumen = {"id": "mis-puntos", "tipo": "puntos", "nombre": datos["nombre"], "saldo": datos["saldo"],
               "nivel": nivel["nombre"] if nivel else None}
    return {"modo": "cliente", "cliente": datos["nombre"], "saldo_puntos": datos["saldo"], "vigentes": vigentes,
            "pasados": pasados, "resultados": [resumen, *vigentes, *pasados]}


def verificar_cupon(texto: str) -> dict:
    """Lee el QR del kiosco: el de cliente (todos sus cupones) o el de un cupón (su estado y los demás
    vigentes de esa persona). Paseito solo consulta, nunca canjea."""
    if not configurado():
        return {"error": "Paseo Points no está conectado en este kiosco.", "resultados": []}
    usuario, problema = cliente_del_qr(texto)
    if problema:
        return {"error": problema, "resultados": []}
    if usuario is not None:
        return cupones_del_cliente(usuario)
    codigo = codigo_cupon(texto)
    if not codigo:
        return {"error": "Ese QR no es de Paseo Points. Muéstrame tu QR de cliente o el de un cupón de la app.",
                "resultados": []}

    def leer(c):
        c.execute(f"{_CONSULTA_CUPON} WHERE r.verificationToken = %s", (codigo,))
        cupon = c.fetchone()
        if not cupon:
            return None, []
        c.execute(f"""{_CONSULTA_CUPON}
                      WHERE r.userId = (SELECT userId FROM Redemption WHERE id = %s)
                        AND r.status = 'PENDING' AND r.id <> %s
                      ORDER BY r.createdAt DESC LIMIT %s""", (cupon["id"], cupon["id"], LIMITE_OTROS_CUPONES))
        return cupon, c.fetchall()

    try:
        cupon, otros = _consultar(leer)
    except pymysql.MySQLError:
        log.exception("Error verificando un cupón de Paseo Points")
        return {"error": f"{NO_DISPONIBLE} Intenta de nuevo en un ratito.", "resultados": []}
    if not cupon:
        return {"error": "No encuentro ese cupón en Paseo Points. Revisa que sea el QR del cupón en la app.",
                "resultados": []}
    tarjeta = _cupon(cupon)
    otras = [_cupon(f) for f in otros]
    return {"cliente": cupon["firstName"], "cupon": tarjeta, "otros_cupones": otras, "resultados": [tarjeta, *otras]}
