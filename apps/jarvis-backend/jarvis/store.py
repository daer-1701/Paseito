"""Versioned local knowledge store. All timestamps are ISO 8601 with timezone."""

from __future__ import annotations

import json
import math
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
    db.execute("CREATE TABLE IF NOT EXISTS session_context (session_id TEXT PRIMARY KEY, record_ids TEXT NOT NULL, updated_at TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS session_preferences (session_id TEXT PRIMARY KEY, preferences TEXT NOT NULL, updated_at TEXT NOT NULL)")
    return db


def parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
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
    for field in ("verified_at", "starts_at", "ends_at"):
        if attrs.get(field):
            parse_timestamp(attrs[field])
    if not isinstance(attrs.get("review_status", "sourced"), str) or attrs.get("review_status", "sourced") not in {"sourced", "approved", "draft", "rejected"}:
        raise ValueError("invalid review_status")
    if record["kind"] in {"event", "promotion"}:
        fields = ("starts_at", "ends_at", "location", "description") if record["kind"] == "event" else (
            "starts_at", "venue_id", "benefit", "terms")
        for field in fields:
            if not isinstance(attrs.get(field), str) or not attrs[field].strip():
                raise ValueError(f"{record['kind']} requires attributes.{field}")
        end = parse_timestamp(attrs.get("ends_at")) if record["kind"] == "event" else expires
        if end <= parse_timestamp(attrs["starts_at"]):
            raise ValueError("end must follow starts_at")
    if record["kind"] == "product" and not attrs.get("venue_id"):
        raise ValueError("products require attributes.venue_id")
    if "price_bs" in attrs and (isinstance(attrs["price_bs"], bool) or
                               not isinstance(attrs["price_bs"], (int, float)) or not math.isfinite(attrs["price_bs"]) or attrs["price_bs"] < 0):
        raise ValueError("price_bs must be a nonnegative number")
    for field in ("products", "services"):
        if field in attrs and (not isinstance(attrs[field], list) or any(not isinstance(v, str) for v in attrs[field])):
            raise ValueError(f"{field} must be a list of strings")
    if attrs.get("review_status") == "approved" and (not attrs.get("verified_at") or not attrs.get("verified_by")):
        raise ValueError("approved records require verified_at and verified_by")
    hours = attrs.get("hours", {})
    if not isinstance(hours, dict):
        raise ValueError("hours must be an object")
    for day, intervals in hours.items():
        if day not in {str(n) for n in range(7)} | {"special"}:
            raise ValueError("hours days must be 0 (Monday) through 6 or special")
        if day == "special":
            if not isinstance(intervals, dict):
                raise ValueError("special schedules must map ISO dates to time pairs")
            from datetime import date
            for special_day in intervals:
                if not isinstance(special_day, str):
                    raise ValueError("special dates must be strings")
                date.fromisoformat(special_day)
        schedules = intervals.values() if day == "special" and isinstance(intervals, dict) else [intervals]
        for schedule in schedules:
            if not isinstance(schedule, list):
                raise ValueError("schedule must be a list of time pairs")
            for pair in schedule:
                if not isinstance(pair, list) or len(pair) != 2 or any(
                    not isinstance(t, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", t) for t in pair):
                    raise ValueError("hours require pairs of HH:MM")
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
    "camisa": {"ropa", "moda"},
    "camisas": {"ropa", "moda"},
    "ninos": {"juegos", "juguetes", "infantil"},
    "regalar": {"regalos", "accesorios", "juguetes"},
    "reunirme": {"reunion", "reuniones", "cowork"},
    "reunirnos": {"reunion", "reuniones", "cowork"},
}


def tokens(value: str) -> set[str]:
    import unicodedata
    value = "".join(c for c in unicodedata.normalize("NFD", value.lower()) if unicodedata.category(c) != "Mn")
    return {t for t in re.findall(r"[a-z0-9]+", value) if len(t) > 2 and t not in STOP}


def search(db: sqlite3.Connection, query: str, limit: int = 5, now: datetime | None = None,
           kinds: set[str] | None = None, event_day=None, browse: bool = False,
           maximum_price=None, venue_ids=None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    terms = tokens(query)
    expanded_terms = {expanded for term in terms for expanded in EXPANSIONS.get(term, set())} - terms
    if not terms and not browse:
        return []
    results = []
    for row in db.execute("SELECT * FROM records"):
        if kinds is not None and row["kind"] not in kinds:
            continue
        if not row["source_url"]:
            continue
        if row["expires_at"] and parse_timestamp(row["expires_at"]) <= now:
            continue
        attrs = json.loads(row["attributes"])
        if row['kind'] == 'venue':
            from .demo import with_demo_hours
            attrs = with_demo_hours(row['id'], attrs)
        if attrs.get('data_origin') == 'synthetic_demo' and os.getenv('JARVIS_DEMO_CATALOG', '0') != '1':
            continue
        if venue_ids is not None and row['kind'] in {'product', 'promotion'} and attrs.get('venue_id') not in venue_ids:
            continue
        if maximum_price is not None and row['kind'] == 'product' and (attrs.get('price_bs') is None or attrs['price_bs'] > maximum_price):
            continue
        if attrs.get("review_status") in {"draft", "rejected"}:
            continue
        if row["kind"] == "promotion" and (not attrs.get("starts_at") or parse_timestamp(attrs["starts_at"]) > now):
            continue
        if row["kind"] == "event":
            if not attrs.get("starts_at") or not attrs.get("ends_at"):
                continue
            start, end = parse_timestamp(attrs["starts_at"]), parse_timestamp(attrs["ends_at"])
            if end <= now:
                continue
            if event_day is not None:
                from .context import BOLIVIA
                from datetime import time, timedelta
                beginning = datetime.combine(event_day, time.min, BOLIVIA)
                if start >= beginning + timedelta(days=1) or end <= beginning:
                    continue
        title_terms = tokens(row["title"])
        body_terms = tokens(row["text"] + " " + " ".join(str(v) for v in attrs.values()))
        score = (4 * len(terms & title_terms) + 2 * len(terms & body_terms)
                 + len(expanded_terms & title_terms) + len(expanded_terms & body_terms))
        if score or browse:
            results.append((score, row["updated_at"], {
                "id": row["id"], "kind": row["kind"], "title": row["title"],
                "text": row["text"], "attributes": attrs, "source_url": row["source_url"],
                "updated_at": row["updated_at"], "expires_at": row["expires_at"],
            }))
    results.sort(key=lambda x: (x[0], x[1]), reverse=True)
    if kinds == {"event"}:
        results.sort(key=lambda x: parse_timestamp(x[2]["attributes"]["starts_at"]))
    return [r for _, _, r in results[:limit]]
