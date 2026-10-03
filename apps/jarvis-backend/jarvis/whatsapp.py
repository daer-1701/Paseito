"""Inbound-only Twilio WhatsApp adapter and an explicitly local presentation fallback."""
import hashlib
import hmac
import json
import os
import re
import threading
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse
from xml.etree.ElementTree import Element, SubElement, tostring
from .agent import chat
from .store import connect

_INCOMING_LOCK = threading.Lock()


def config_status():
    url = urlparse(os.getenv('JARVIS_WHATSAPP_WEBHOOK_URL', ''))
    url_ready = url.scheme == 'https' and bool(url.netloc) and url.path == '/whatsapp/webhook' and not url.query and not url.fragment
    provider = os.getenv('JARVIS_WHATSAPP_PROVIDER', 'disabled')
    return {'provider': provider, 'configured': provider == 'twilio' and url_ready and bool(os.getenv('TWILIO_AUTH_TOKEN')),
            'https_url_configured': url_ready, 'credential_configured': bool(os.getenv('TWILIO_AUTH_TOKEN')),
            'local_demo_enabled': os.getenv('JARVIS_DEMO_CATALOG') == '1',
            'delivery_verified': False,
            'note': 'Configuración disponible no acredita entrega. Verificar WhatsApp real desde un participante antes de presentar.'}


class FormValues(dict):
    def getall(self, key):
        return self[key]


def validate_twilio(raw_body, signature, request_path):
    if not config_status()['configured']:
        raise RuntimeError('WhatsApp connector is not configured')
    url = os.environ['JARVIS_WHATSAPP_WEBHOOK_URL']
    if request_path != '/whatsapp/webhook':
        raise ValueError('unexpected webhook path')
    params = FormValues(parse_qs(raw_body.decode('utf-8'), keep_blank_values=True, max_num_fields=100))
    from twilio.request_validator import RequestValidator
    if not signature or not RequestValidator(os.environ['TWILIO_AUTH_TOKEN']).validate(url, params, signature):
        raise PermissionError('invalid webhook signature')
    def single(name):
        values = params.get(name, [])
        if len(values) != 1:
            raise ValueError('missing or repeated message field')
        return values[0]
    sender, sid = single('From'), single('MessageSid')
    if not re.fullmatch(r'whatsapp:\+[1-9]\d{5,14}', sender) or not re.fullmatch(r'(?:SM|MM)[a-fA-F0-9]{32}', sid):
        raise ValueError('invalid WhatsApp sender or message ID')
    if params.get('NumMedia', ['0'])[0] != '0':
        return sender, sid, None
    return sender, sid, single('Body')


def opaque_session(identity, channel):
    secret = os.getenv('JARVIS_WHATSAPP_SESSION_SECRET') or os.getenv('JARVIS_INGEST_TOKEN')
    if not secret:
        raise RuntimeError('session secret is not configured')
    digest = hmac.new(secret.encode(), f'{channel}:{identity}'.encode(), hashlib.sha256).hexdigest()
    return 'wa-' + digest[:48]


def incoming(identity, sid, message, channel='twilio'):
    if not isinstance(sid, str) or not 1 <= len(sid) <= 100:
        raise ValueError('invalid message ID')
    if message is not None and (not isinstance(message, str) or not message.strip() or len(message) > 2000):
        raise ValueError('message must contain 1 to 2000 characters')
    session = opaque_session(identity, channel)
    fingerprint = hashlib.sha256((session + ':' + (message or '<media>')).encode()).hexdigest()
    # A single adapter process serializes incoming work, preventing concurrent retry replies.
    with _INCOMING_LOCK, connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS whatsapp_inbox (message_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, result TEXT NOT NULL, created_at TEXT NOT NULL)')
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        db.execute('DELETE FROM whatsapp_inbox WHERE created_at < ?', (cutoff,))
        db.commit()
        key = channel + ':' + sid
        existing = db.execute('SELECT fingerprint, result FROM whatsapp_inbox WHERE message_id=?', (key,)).fetchone()
        if existing:
            if existing['fingerprint'] != fingerprint:
                raise ValueError('message ID reused with different content')
            return {**json.loads(existing['result']), 'duplicate': True}
        first = not db.execute('SELECT 1 FROM turns WHERE session_id=? LIMIT 1', (session,)).fetchone()
        if message is None:
            result = {'answer': 'Por ahora puedo conversar por texto. Escríbeme qué tienda o producto buscas.', 'sources': [], 'suggestions': [], 'session_id': session}
        elif message.strip().lower() in {'reiniciar', '/reiniciar', 'nuevo'}:
            for table in ('turns', 'session_context', 'session_preferences'):
                db.execute(f'DELETE FROM {table} WHERE session_id=?', (session,))
            db.commit()
            result = {'answer': 'Empecemos de nuevo. ¿Qué tienda, producto o promoción quieres encontrar?', 'sources': [], 'suggestions': [], 'session_id': session}
        else:
            try:
                result = chat(db, message, session, allow_external=False)
            except Exception as exc:
                db.rollback()
                print(f'WhatsApp response fallback: {type(exc).__name__}', flush=True)
                result = {'answer': 'Tuve un problema al consultar esa información. Puedes escribirme de nuevo o usar el kiosco de Jarvis.', 'sources': [], 'suggestions': [], 'session_id': session, 'fallback': True}
        text = result['answer']
        if first and channel == 'twilio' and os.getenv('JARVIS_DEMO_CATALOG') == '1':
            text = 'Jarvis · modo demo\n\n' + text
        choices = result.get('suggestions', [])[:3]
        if result.get('dialogue_stage') == 'shops' and choices:
            text += '\n\n' + '\n'.join(f'{i}. {name}' for i, name in enumerate(choices, 1))
            text += '\nResponde con el nombre o el número de la tienda.'
        result['channel_answer'] = text
        result['duplicate'] = False
        db.execute('INSERT INTO whatsapp_inbox VALUES (?, ?, ?, ?)',
                   (key, fingerprint, json.dumps(result, ensure_ascii=False), datetime.now(timezone.utc).isoformat()))
        db.commit()
        return result


def twiml(result):
    root = Element('Response')
    if not result.get('duplicate'):
        SubElement(root, 'Message').text = result['channel_answer']
    return tostring(root, encoding='utf-8', xml_declaration=True)
