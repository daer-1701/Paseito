"""Coupon reader adapted from daer-1701's 6a28f76 to the unified Points reader.

Only queries. Raw QR tokens, customer names and balances never enter the LLM.
The caller binds validated identity to a short-lived conversation capability.
"""
import base64
import hashlib
import hmac
import json
import os
import re
import time
import math
import urllib.error
import urllib.request
from urllib.parse import urlparse

import pymysql
from . import puntos
from .config import PUNTOS_API_URL, PUNTOS_API_KEY, PUNTOS_QR_SECRET, PUNTOS_TIMEOUT_S

CODIGO_CUPON = re.compile(r'\b[A-Z0-9]{5}-[A-Z0-9]{5}\b', re.I)
QR_CLIENTE = re.compile(r'PP1\.([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)')
QR_NO_VALIDO = 'No pude validar ese QR. Abre tu QR de cliente en Paseo Points y muéstramelo de nuevo.'
QR_VENCIDO = 'Ese QR ya venció. Abre uno nuevo en la app de Paseo Points.'
ESTADOS = {'PENDING':'vigente','REDEEMED':'canjeado','EXPIRED':'vencido','CANCELLED':'cancelado'}
CONSULTA = '''SELECT r.id, r.status, r.pointsSpent, r.createdAt, r.redeemedAt,
    w.type, w.discountAmount, w.discountPercent, w.quantity, w.minimumPurchase, w.description,
    ci.name AS producto, b.name AS negocio, b.floor, b.localNumber, b.sector
    FROM Redemption r JOIN Reward w ON w.id = r.rewardId
    LEFT JOIN CatalogItem ci ON ci.id = w.catalogItemId
    LEFT JOIN Business b ON b.id = COALESCE(r.businessId, w.businessId)'''


def _b64(text):
    return base64.urlsafe_b64decode(text + '=' * (-len(text) % 4))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def cliente_del_qr(text):
    found = QR_CLIENTE.search(text)
    if not found: return None, None
    if PUNTOS_API_URL and PUNTOS_API_KEY:
        target=urlparse(PUNTOS_API_URL)
        if target.scheme!='https' and not (target.scheme=='http' and target.hostname in {'localhost','127.0.0.1','::1'}):
            return None, 'La API de Points necesita HTTPS (HTTP solo en localhost para desarrollo).'
        request = urllib.request.Request(PUNTOS_API_URL+'/api/integrations/customer-qr/verify',
            data=json.dumps({'token':found.group(0)}).encode(), method='POST',
            headers={'Content-Type':'application/json','x-api-key':PUNTOS_API_KEY})
        try:
            with urllib.request.build_opener(_NoRedirect()).open(request, timeout=PUNTOS_TIMEOUT_S) as response:
                raw = response.read(65537)
                if len(raw)>65536: return None, QR_NO_VALIDO
                user = json.loads(raw)['userId']
                if isinstance(user,bool) or not str(user).isdigit() or int(user)<=0: return None, QR_NO_VALIDO
                return int(user), None
        except urllib.error.HTTPError as exc:
            return None, QR_VENCIDO if exc.code==410 else QR_NO_VALIDO
        except (OSError,ValueError,KeyError,TypeError):
            return None, 'No pude conectar con la verificación de Points. Intenta nuevamente.'
    if PUNTOS_QR_SECRET:
        try:
            data, signature = found.groups()
            expected = hmac.new(PUNTOS_QR_SECRET.encode(), data.encode(), hashlib.sha256).digest()
            if not hmac.compare_digest(expected, _b64(signature)): return None, QR_NO_VALIDO
            payload = json.loads(_b64(data))
            user, expires = payload['u'], float(payload['exp'])/1000
            if isinstance(user,bool) or not str(user).isdigit() or int(user)<=0 or not math.isfinite(expires): return None, QR_NO_VALIDO
            if expires<=time.time(): return None, QR_VENCIDO
            return int(user), None
        except (ValueError,KeyError,TypeError,OverflowError):
            return None, QR_NO_VALIDO
    return None, 'La validación del QR de cliente todavía no está configurada. Puedes consultar el código de un cupón.'


def _tarjeta(row):
    return {'id':f"cupon-{row['id']}", 'tipo':'cupon', 'titulo':puntos._beneficio(row),
        'detalle':row['description'] or '', 'estado':ESTADOS.get(row['status'],str(row['status']).lower()),
        'puntos_usados':puntos._num(row['pointsSpent']), 'nombre':row['negocio'] or 'Paseo Points',
        'obtenido_el':puntos._local(row['createdAt']), 'canjeado_el':puntos._local(row['redeemedAt']),
        'ubicacion':{'piso':row['floor'] or '', 'local':row['localNumber'] or '', 'sector':row['sector'] or ''}}


def _respuesta(cards, mode, demo=False):
    valid = [c for c in cards if c['estado']=='vigente']
    if mode=='cliente':
        answer = f"Tienes {len(valid)} cupón{'es' if len(valid)!=1 else ''} vigente{'s' if len(valid)!=1 else ''}."
        if valid: answer += ' '+ '; '.join(f"{c['titulo']} en {c['nombre']}" for c in valid[:3])+'.'
    else:
        c=cards[0]
        answer=f"Tu cupón de {c['titulo']} está {c['estado']}. Se utiliza en {c['nombre']}."
    answer += ' El canje se realiza en Paseo Points o en el comercio.'
    if mode=='cupon' and not demo:
        answer += ' Para ver otros cupones, usa tu QR de cliente o la web de Paseo Points.'
    return {'modo':mode,'resultados':cards,'vigentes':valid,'respuesta':answer,'demo':demo,'read_only':True}


def status():
    return {'external_connected':puntos.configurado(),
        'customer_qr_validation':bool((PUNTOS_API_URL and PUNTOS_API_KEY) or PUNTOS_QR_SECRET),
        'demo_enabled':os.getenv('JARVIS_DEMO_CATALOG')=='1','read_only':True}


def verificar(text):
    if not isinstance(text,str) or not 1<=len(text.strip())<=500:
        raise ValueError('El código debe tener entre 1 y 500 caracteres')
    text=text.strip()
    if text=='DEMO-PUNTOS' and status()['demo_enabled']:
        return {'modo':'cliente','resultados':[],'respuesta':'Identidad de ejemplo activada para esta conversación. Puedes preguntar cuántos puntos tienes.',
            'demo':True,'read_only':True,'_verified_demo':True}
    if text=='DEMO-PASEITO' and status()['demo_enabled']:
        card={'id':'cupon-demo','tipo':'cupon','titulo':'10 % de descuento en pizza familiar',
            'detalle':'Ejemplo de lectura; no se puede canjear.','estado':'vigente',
            'puntos_usados':100,'nombre':'Almacén de Pizzas','demo':True,
            'ubicacion':{'piso':'3','local':'311','sector':'centro comercial'}}
        result=_respuesta([card],'cupon',True)
        result['respuesta']='Te muestro un ejemplo de cupón: 10 % de descuento en pizza familiar. Esta lectura es de demostración y no permite canjear.'
        return result
    user, problem=cliente_del_qr(text)
    if problem: return {'error':problem+' Puedes continuar desde la web de Paseo Points.','resultados':[],'read_only':True}
    if not puntos.configurado():
        return {'error':'Paseo Points no está conectado en este kiosco. Consulta desde la web de Paseo Points o revisa el ejemplo local.','resultados':[],'read_only':True}
    code=CODIGO_CUPON.search(text)
    if user is None and not code:
        return {'error':'Ese QR no es de Paseo Points. Usa el QR de cliente o de un cupón de la app.','resultados':[],'read_only':True}
    def read(cursor):
        if user is not None:
            cursor.execute("SELECT id FROM User WHERE id=%s AND role='CUSTOMER' AND status='ACTIVE' AND deletedAt IS NULL",(user,))
            if not cursor.fetchone():return None
            cursor.execute(CONSULTA+" WHERE r.userId=%s ORDER BY (r.status='PENDING') DESC, r.createdAt DESC LIMIT 20",(user,))
            return cursor.fetchall()
        cursor.execute(CONSULTA+' WHERE r.verificationToken=%s',(code.group(0).upper(),))
        row=cursor.fetchone()
        return [row] if row else []
    try: rows=puntos._consultar(read)
    except pymysql.MySQLError:
        return {'error':puntos.NO_DISPONIBLE+' Hice un intento; consulta desde la web de Paseo Points.','resultados':[],'read_only':True}
    if rows is None or not rows and user is None:
        return {'error':'No encuentro cupones para ese QR o código en Paseo Points.','resultados':[],'read_only':True}
    result=_respuesta([_tarjeta(r) for r in rows],'cliente' if user is not None else 'cupon')
    if user is not None:result['_verified_user_id']=user
    result['personal']=True
    return result
