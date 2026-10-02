"""Minimal JSON HTTP API with no third-party dependencies."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

from .agent import chat
from .store import connect, delete, upsert


class Handler(BaseHTTPRequestHandler):
    server_version = "JarvisPaseo/0.1"

    def send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", os.getenv("JARVIS_CORS_ORIGIN", "*"))
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_json(204, {})

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
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
        if urlparse(self.path).path == "/health":
            with connect() as db:
                count = db.execute("SELECT count(*) FROM records").fetchone()[0]
            self.send_json(200, {"status": "ok", "records": count})
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
        server.serve_forever()


if __name__ == "__main__":
    main()
