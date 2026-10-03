"""Import a sourced starter directory for the Paseo Aranjuez demo."""

import json
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .store import connect, delete, upsert, validate_record


CATALOG = Path(__file__).resolve().parents[1] / "data" / "venues.json"
OLD_DEMO_IDS = ("venue:demo-cafe", "venue:demo-regalos", "product:demo-taza")


def main() -> None:
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] != "--refresh"):
        raise SystemExit("usage: python3 -m jarvis.seed [--refresh]")
    refresh = len(sys.argv) == 2
    records = json.loads(CATALOG.read_text(encoding="utf-8"))
    if not isinstance(records, list) or len(records) != 20:
        raise ValueError("starter catalog must contain 20 venues")
    updated = datetime.now(timezone.utc).isoformat()
    prepared = []
    for record in records:
        if record.get("kind") != "venue" or not record.get("source_url"):
            raise ValueError("each venue needs a source URL")
        prepared.append(validate_record({**record, "updated_at": record.get('updated_at', updated)}))
    loaded = 0
    with closing(connect()) as db:
        for record_id in OLD_DEMO_IDS:
            delete(db, record_id)
        for record in prepared:
            exists = db.execute("SELECT 1 FROM records WHERE id=?", (record["id"],)).fetchone()
            if refresh or not exists:
                upsert(db, record)
                loaded += 1
    print(f"Loaded {loaded} sourced Paseo Aranjuez venues ({len(records)} in starter catalog)")


if __name__ == "__main__":
    main()
