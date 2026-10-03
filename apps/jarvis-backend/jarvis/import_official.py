"""Import the official Paseo Aranjuez directory as source-backed venue records."""

from __future__ import annotations

import json
import re
import unicodedata
import urllib.request
from datetime import datetime, timezone

from .store import connect, upsert


DIRECTORY_URL = "https://paseoaranjuez.com/stores"


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    return "".join(char for char in value if unicodedata.category(char) != "Mn" and char.isalnum())


def readable(value: object) -> str:
    text = str(value or "").strip()
    if "Ã" in text or "Â" in text:
        for encoding in ("cp1252", "latin-1"):
            try:
                return text.encode(encoding).decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
    return text


def record_id(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", normalized(title)).strip("-")
    return f"venue:official-{slug}"


def fetch_directory() -> list[dict]:
    request = urllib.request.Request(DIRECTORY_URL, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"official directory returned HTTP {response.status}")
        body = response.read(2_000_000)
    result = json.loads(body)
    if not isinstance(result, list):
        raise ValueError("official directory must be a JSON list")
    return result


def import_directory(db, stores: list[dict], observed_at: str | None = None) -> int:
    observed_at = observed_at or datetime.now(timezone.utc).isoformat()
    existing = {normalized(row[0]) for row in db.execute("SELECT title FROM records WHERE kind='venue'")}
    added = 0
    for store in stores:
        title = readable(store.get("title"))
        if not title:
            continue
        canonical = normalized(title)
        if any(canonical in known or known in canonical for known in existing):
            continue
        floor = readable(store.get("floor"))
        categories = [readable(category) for category in store.get("categories", []) if readable(category)]
        category = ", ".join(categories) or "negocio"
        text = f"Negocio del directorio oficial del Paseo Aranjuez. Categoría: {category}."
        attributes = {
            "category": category,
            "floor": floor,
            "source_type": "official_directory",
            "observed_at": observed_at,
            "review_status": "sourced",
        }
        upsert(db, {
            "id": record_id(title), "kind": "venue", "title": title, "text": text,
            "attributes": attributes, "source_url": DIRECTORY_URL, "updated_at": observed_at,
        })
        existing.add(canonical)
        added += 1
    return added


def main() -> None:
    stores = fetch_directory()
    with connect() as db:
        added = import_directory(db, stores)
    print(f"Imported {added} official venues from {len(stores)} directory entries")


if __name__ == "__main__":
    main()
