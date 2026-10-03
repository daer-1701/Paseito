"""Minimal JSON HTTP API with public destination pages and locally generated QR."""

import json
import mimetypes
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import unquote, urlparse

from .agent import chat
from .quality import report
from .destination import destination_page
from .qr import destination_qr
from .stimulus import gaze
from .whatsapp import config_status as whatsapp_status, validate_twilio, incoming as whatsapp_incoming, twiml
from .store import connect, delete, upsert
from .voice import MAX_AUDIO_BYTES, VoiceUnavailable, status as voice_status, synthesize, transcribe, stream_speech


WEB_DIR = Path(__file__).resolve().parents[1] / "web"
KIOSK_DIR = WEB_DIR / "kiosk"


def kiosk_asset(path: str) -> Optional[Tuple[Path, str]]:
    relative = "index.html" if path in {"/", ""} else path.lstrip("/")
    candidate = (KIOSK_DIR / relative).resolve()
    if KIOSK_DIR.resolve() not in candidate.parents or not candidate.is_file():
        return None
    mime = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
    if candidate.suffix == ".js":
        mime = "text/javascript; charset=utf-8"
    elif candidate.suffix == ".html":
        mime = "text/html; charset=utf-8"
    return candidate, mime


class Handler(BaseHTTPRequestHandler):
    server_version = "JarvisPaseo/0.1"

    def send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        allowed_origin = os.getenv("JARVIS_CORS_ORIGIN")
        if allowed_origin and self.headers.get("Origin") == allowed_origin:
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status: int, data: dict) -> None:
        self.send_bytes(status, json.dumps(data, ensure_ascii=False).encode("utf-8"),
                        "application/json; charset=utf-8")

    def do_OPTIONS(self) -> None:
        self.send_json(204, {})

    def read_json(self) -> dict:
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            raise ValueError("Content-Type must be application/json")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if length < 1 or length > 65536:
            raise ValueError("body must contain 1 to 65536 bytes")
        data = json.loads(self.rfile.read(length))
        if not isinstance(data, dict):
            raise ValueError("body must be a JSON object")
        return data

    def authorized(self) -> bool:
        secret = os.getenv("JARVIS_INGEST_TOKEN")
        return bool(secret and self.headers.get("Authorization") == f"Bearer {secret}")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            with connect() as db:
                count = db.execute("SELECT count(*) FROM records").fetchone()[0]
            self.send_json(200, {"status": "ok", "records": count,
                                 "openai_configured": bool(os.getenv("OPENAI_API_KEY"))})
        elif path == "/admin/quality":
            if not self.authorized():
                self.send_json(401, {"error": "unauthorized"})
                return
            with connect() as db:
                self.send_json(200, report(db))
        elif path.startswith('/qr/destination/'):
            with connect() as db:
                svg = destination_qr(db, unquote(path.removeprefix('/qr/destination/')))
            if svg is None:
                self.send_json(404, {'error': 'destination QR unavailable'})
            else:
                self.send_bytes(200, svg, 'image/svg+xml')
        elif path.startswith('/destination/'):
            with connect() as db:
                page = destination_page(db, unquote(path.removeprefix('/destination/')))
            if page is None:
                self.send_json(404, {'error': 'destination unavailable'})
            else:
                self.send_bytes(200, page.encode('utf-8'), 'text/html; charset=utf-8')
        elif path == "/kiosk/config":
            self.send_json(200, {"origin": os.getenv("JARVIS_KIOSK_ORIGIN", "Punto del kiosco pendiente de configurar"),
                "public_base_url": os.getenv('JARVIS_MOBILE_BASE_URL', ''),
                "demo_catalog": os.getenv('JARVIS_DEMO_CATALOG') == '1'})
        elif path == '/whatsapp/status':
            self.send_json(200, whatsapp_status())
        elif path == '/whatsapp/demo':
            if os.getenv('JARVIS_DEMO_CATALOG') != '1':
                self.send_json(404, {'error': 'demo unavailable'})
            else:
                self.send_bytes(200, (WEB_DIR / 'whatsapp.html').read_bytes(), 'text/html; charset=utf-8')
        elif path == '/catalog/demo':
            self.send_bytes(200, '<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Modo demo</title><main style="font:18px/1.6 system-ui;max-width:650px;margin:40px auto;padding:20px"><h1>Modo demo</h1><p>El catálogo, sus precios y promociones, y los horarios que faltaban son datos de prueba para demostrar Jarvis. No constituyen ofertas, inventario confirmado ni horarios oficiales. Los horarios reales ya documentados se conservan. Los nombres y ubicaciones de los negocios provienen de las fuentes públicas citadas en sus fichas.</p><a href="/">Volver a Jarvis</a></main></html>'.encode('utf-8'), 'text/html; charset=utf-8')
        elif path == "/voice/status":
            self.send_json(200, voice_status())
        elif path in {"/", "/kiosk", "/kiosk/"}:
            asset = kiosk_asset("/")
            if not asset:
                self.send_json(404, {"error": "kiosk assets not found"})
                return
            self.send_bytes(200, asset[0].read_bytes(), asset[1])
        elif path.startswith("/kiosk/"):
            asset = kiosk_asset(path.removeprefix("/kiosk/"))
            if not asset:
                self.send_json(404, {"error": "not found"})
                return
            self.send_bytes(200, asset[0].read_bytes(), asset[1])
        elif path.startswith("/js/") or path.startswith("/vendor/"):
            # Allows a browser holding an older cached kiosk HTML page to
            # recover its avatar assets after the server is upgraded.
            asset = kiosk_asset(path.lstrip("/"))
            if not asset:
                self.send_json(404, {"error": "not found"})
                return
            self.send_bytes(200, asset[0].read_bytes(), asset[1])
        elif path in {"/simple", "/app.js"}:
            filename = "index.html" if path == "/" else "app.js"
            if path == "/simple":
                filename = "index.html"
            mime = "text/html; charset=utf-8" if path == "/" else "text/javascript; charset=utf-8"
            if path == "/simple":
                mime = "text/html; charset=utf-8"
            self.send_bytes(200, (WEB_DIR / filename).read_bytes(), mime)
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == '/whatsapp/webhook':
            try:
                if self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/x-www-form-urlencoded':
                    raise ValueError('form content type required')
                length = int(self.headers.get('Content-Length', '0'))
                if not 1 <= length <= 65536:
                    raise ValueError('invalid form body length')
                sender, sid, message = validate_twilio(self.rfile.read(length), self.headers.get('X-Twilio-Signature'), self.path)
                result = whatsapp_incoming(sender, sid, message)
                self.send_bytes(200, twiml(result), 'application/xml; charset=utf-8')
            except PermissionError:
                self.send_json(403, {'error': 'invalid signature'})
            except RuntimeError:
                self.send_json(503, {'error': 'WhatsApp connector not configured'})
            except (ValueError, UnicodeDecodeError):
                self.send_json(400, {'error': 'invalid webhook message'})
        elif path == '/whatsapp/demo/message':
            if os.getenv('JARVIS_DEMO_CATALOG') != '1':
                self.send_json(404, {'error': 'demo unavailable'})
                return
            try:
                payload = self.read_json()
                identity = payload.get('session_id')
                if not isinstance(identity, str) or not re.fullmatch(r'[a-zA-Z0-9-]{8,80}', identity):
                    raise ValueError('invalid demo session')
                result = whatsapp_incoming(identity, payload.get('message_id'), payload.get('message'), 'local_demo')
                self.send_json(200, {'answer': result['channel_answer'], 'suggestions': result.get('suggestions', []),
                                     'duplicate': result['duplicate'], 'local_only': True})
            except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
                self.send_json(400, {'error': str(exc)})
        elif path == "/voice/stream":
            stream = None
            started = False
            try:
                payload = self.read_json()
                stream = stream_speech(payload.get("text"))
                first = next(stream, None)
                if not first:
                    raise VoiceUnavailable("empty speech stream")
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Accel-Buffering", "no")
                self.send_header("Connection", "close")
                self.end_headers()
                started = True
                self.wfile.write(first)
                self.wfile.flush()
                for chunk in stream:
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            except (ValueError, VoiceUnavailable) as exc:
                if not started:
                    self.send_json(400 if isinstance(exc, ValueError) else 503, {"error": str(exc)})
                # After headers, close the incomplete stream; never append a second HTTP response.
            finally:
                self.close_connection = True
                if stream:
                    stream.close()
        elif path == "/chat":
            try:
                payload = self.read_json()
                with connect() as db:
                    result = chat(db, payload.get("message"), payload.get("session_id"))
                self.send_json(200, result)
            except (ValueError, json.JSONDecodeError) as exc:
                self.send_json(400, {"error": str(exc)})
        elif path == "/voice/transcribe":
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_json(400, {"error": "invalid Content-Length"})
                return
            if not 44 <= length <= MAX_AUDIO_BYTES:
                self.send_json(400, {"error": "audio must be a short PCM WAV recording"})
                return
            try:
                transcript = transcribe(self.rfile.read(length))
                self.send_json(200, {"text": transcript})
            except ValueError as exc:
                self.send_json(400, {"error": str(exc)})
            except VoiceUnavailable as exc:
                self.send_json(503, {"error": str(exc)})
        elif path == "/voice/synthesize":
            try:
                payload = self.read_json()
                audio, mime = synthesize(payload.get("text"))
                self.send_bytes(200, audio, mime)
            except (ValueError, json.JSONDecodeError) as exc:
                self.send_json(400, {"error": str(exc)})
            except VoiceUnavailable as exc:
                self.send_json(503, {"error": str(exc)})
        elif path == "/stimulus/gaze":
            try:
                payload = self.read_json()
                with connect() as db:
                    result = gaze(db, payload.get("session_id"), payload.get("target_id"),
                                  payload.get("dwell_ms"))
                self.send_json(200, result)
            except (ValueError, json.JSONDecodeError) as exc:
                self.send_json(400, {"error": str(exc)})
        elif path == "/admin/records":
            if not self.authorized():
                self.send_json(401, {"error": "unauthorized"})
                return
            try:
                payload = self.read_json()
                with connect() as db:
                    upsert(db, payload)
                self.send_json(200, {"id": payload["id"], "status": "upserted"})
            except (ValueError, KeyError, json.JSONDecodeError) as exc:
                self.send_json(400, {"error": str(exc)})
        else:
            self.send_json(404, {"error": "not found"})

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        if path.startswith("/chat/"):
            session_id = unquote(path.removeprefix("/chat/"))
            with connect() as db:
                db.execute("DELETE FROM turns WHERE session_id=?", (session_id,))
                db.execute("DELETE FROM session_context WHERE session_id=?", (session_id,))
                db.execute("DELETE FROM session_preferences WHERE session_id=?", (session_id,))
                db.commit()
            self.send_json(200, {"deleted": True})
            return
        if not path.startswith("/admin/records/"):
            self.send_json(404, {"error": "not found"})
            return
        if not self.authorized():
            self.send_json(401, {"error": "unauthorized"})
            return
        record_id = unquote(path.removeprefix("/admin/records/"))
        with connect() as db:
            found = delete(db, record_id)
        self.send_json(200 if found else 404, {"id": record_id, "deleted": found})


def main() -> None:
    host = os.getenv("JARVIS_HOST", "127.0.0.1")
    port = int(os.getenv("JARVIS_PORT", "8000"))
    with ThreadingHTTPServer((host, port), Handler) as server:
        print(f"Jarvis listening at http://{host}:{port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
