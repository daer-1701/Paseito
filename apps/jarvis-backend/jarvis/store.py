"""Versioned local knowledge store. All timestamps are ISO 8601 with timezone."""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def db_path() -> Path:
    return Path(os.getenv("JARVIS_DB", Path(__file__).resolve().parents[1] / "jarvis.sqlite3"))


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            attributes TEXT NOT NULL,
            source_url TEXT,
            updated_at TEXT NOT NULL,
            expires_at TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id, id)")
    return db


def parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamps require a timezone")
    return dt


def validate_record(record: dict) -> dict:
    required = ("id", "kind", "title", "text", "updated_at")
    for key in required:
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise ValueError(f"{key} is required")
    if record["kind"] not in {"venue", "product", "promotion", "event", "faq"}:
        raise ValueError("invalid kind")
    updated = parse_timestamp(record["updated_at"])
    expires = parse_timestamp(record.get("expires_at"))
    if expires and expires <= updated:
        raise ValueError("expires_at must follow updated_at")
    if record["kind"] == "promotion" and not expires:
        raise ValueError("promotions require expires_at")
    attrs = record.get("attributes", {})
    if not isinstance(attrs, dict):
        raise ValueError("attributes must be an object")
    url = record.get("source_url")
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        raise ValueError("source_url is required and must be an HTTP URL")
    return {**record, "attributes": attrs, "source_url": url,
            "updated_at": updated.astimezone(timezone.utc).isoformat(),
            "expires_at": expires.astimezone(timezone.utc).isoformat() if expires else None}


def upsert(db: sqlite3.Connection, record: dict) -> None:
    r = validate_record(record)
    db.execute("""
        INSERT INTO records (id, kind, title, text, attributes, source_url, updated_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          kind=excluded.kind, title=excluded.title, text=excluded.text,
          attributes=excluded.attributes, source_url=excluded.source_url,
          updated_at=excluded.updated_at, expires_at=excluded.expires_at
        WHERE excluded.updated_at >= records.updated_at
    """, (r["id"], r["kind"], r["title"], r["text"], json.dumps(r["attributes"], ensure_ascii=False),
          r["source_url"], r["updated_at"], r["expires_at"]))
    db.commit()


def delete(db: sqlite3.Connection, record_id: str) -> bool:
    cursor = db.execute("DELETE FROM records WHERE id=?", (record_id,))
    db.commit()
    return cursor.rowcount > 0


STOP = {"de", "del", "la", "el", "los", "las", "un", "una", "y", "o", "en", "para", "por", "que", "quiero", "necesito", "hay", "donde", "está", "esta", "me", "puedes", "algo", "con"}

EXPANSIONS = {
    "comer": {"comida", "restaurante", "cafe", "gastronomia"},
    "hambre": {"comida", "restaurante", "cafe", "gastronomia"},
    "almorzar": {"comida", "restaurante", "gastronomia"},
    "cenar": {"comida", "restaurante", "gastronomia"},
    "regalo": {"regalos", "accesorios"},
    "cafe": {"cafeteria"},
    "pizza": {"pizzas", "pizzeria"},
}


def tokens(value: str) -> set[str]:
    import unicodedata
    value = "".join(c for c in unicodedata.normalize("NFD", value.lower()) if unicodedata.category(c) != "Mn")
    return {t for t in re.findall(r"[a-z0-9]+", value) if len(t) > 2 and t not in STOP}


def search(db: sqlite3.Connection, query: str, limit: int = 5, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    terms = tokens(query)
    expanded_terms = {expanded for term in terms for expanded in EXPANSIONS.get(term, set())} - terms
    if not terms:
        return []
    results = []
    for row in db.execute("SELECT * FROM records"):
        if not row["source_url"]:
            continue
        if row["expires_at"] and parse_timestamp(row["expires_at"]) <= now:
            continue
        attrs = json.loads(row["attributes"])
        title_terms = tokens(row["title"])
        body_terms = tokens(row["text"] + " " + " ".join(str(v) for v in attrs.values()))
        score = (4 * len(terms & title_terms) + 2 * len(terms & body_terms)
                 + len(expanded_terms & title_terms) + len(expanded_terms & body_terms))
        if score:
            results.append((score, row["updated_at"], {
                "id": row["id"], "kind": row["kind"], "title": row["title"],
                "text": row["text"], "attributes": attrs, "source_url": row["source_url"],
                "updated_at": row["updated_at"], "expires_at": row["expires_at"],
            }))
    results.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [r for _, _, r in results[:limit]]
