"""Idempotent container startup: seed missing public records, then serve."""
import json
import os
from contextlib import closing
from pathlib import Path

from .seed import main as seed
from .store import connect, upsert
from .import_records import load_bundle


def load_catalog():
    seed()
    snapshot = Path(__file__).resolve().parents[1] / "data" / "official-snapshot.json"
    if snapshot.exists():
        with closing(connect()) as db:
            for record in json.loads(snapshot.read_text(encoding="utf-8")):
                if not db.execute("SELECT 1 FROM records WHERE id=?", (record["id"],)).fetchone():
                    upsert(db, record)
    with closing(connect()) as db:
        load_bundle(db, Path(__file__).resolve().parents[1] / "data" / "public-services.json", missing_only=True)
        # Dated source research is versioned; newer editorial changes win in upsert.
        research = Path(__file__).resolve().parents[1] / "data" / "research-2026-10-03.json"
        if research.exists():
            load_bundle(db, research)
        if os.getenv('JARVIS_DEMO_CATALOG') == '1':
            load_bundle(db, Path(__file__).resolve().parents[1] / 'data' / 'demo-catalog.json')
            load_bundle(db, Path(__file__).resolve().parents[1] / 'data' / 'demo-promotions.json')
        # Legacy imports called source observation "verified_at", without human approval.
        for row in db.execute("SELECT id, attributes FROM records WHERE kind='venue'").fetchall():
            attrs = json.loads(row['attributes'])
            if attrs.get('source_type') == 'official_directory' and attrs.get('verified_at') and attrs.get('review_status') != 'approved':
                attrs['observed_at'] = attrs.pop('verified_at')
                attrs.setdefault('review_status', 'sourced')
                db.execute('UPDATE records SET attributes=? WHERE id=?', (json.dumps(attrs, ensure_ascii=False), row['id']))
        db.commit()
        companion = Path(__file__).resolve().parents[1] / 'data' / 'companion-2026-10-03.json'
        if companion.exists():
            # Correct the timestamp of the first local migration build (UTC offset typo).
            for row in db.execute("SELECT id, attributes FROM records WHERE updated_at='2026-10-03T22:00:00+00:00'").fetchall():
                if json.loads(row['attributes']).get('companion_import') == '28b9729':
                    db.execute("UPDATE records SET updated_at='2026-10-03T18:00:00+00:00' WHERE id=?", (row['id'],))
            db.commit()
            load_bundle(db, companion)


def main():
    # Compatibility entry point; there is only one HTTP implementation.
    import sys
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / 'backend'))
    from app.main import run
    run()


if __name__ == "__main__":
    main()
