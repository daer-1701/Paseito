"""Minimal JSON HTTP API with no third-party dependencies."""

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import unquote, urlparse

from .agent import chat
from .stimulus import gaze
from .store import connect, delete, upsert
from .voice import MAX_AUDIO_BYTES, VoiceUnavailable, status as voice_status, synthesize, transcribe


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
        if path == "/chat":
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
