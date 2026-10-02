"""Idempotent container startup: seed missing public records, then serve."""
import json
from pathlib import Path

from .api import main as serve
from .seed import main as seed
from .store import connect, upsert


def main():
    seed()
    snapshot = Path(__file__).resolve().parents[1] / "data" / "official-snapshot.json"
    if snapshot.exists():
        with connect() as db:
            for record in json.loads(snapshot.read_text(encoding="utf-8")):
                if not db.execute("SELECT 1 FROM records WHERE id=?", (record["id"],)).fetchone():
                    upsert(db, record)
    serve()


if __name__ == "__main__":
    main()
