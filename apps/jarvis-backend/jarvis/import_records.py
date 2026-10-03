"""Validate a JSON knowledge bundle before loading it. No simulated data by default."""
import argparse
import json
from pathlib import Path
from .store import connect, upsert, validate_record


def load_bundle(db, path, missing_only=False):
    raw = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(raw, list):
        raise ValueError('bundle must be a JSON list')
    if any(not isinstance(r,dict) for r in raw):
        raise ValueError('bundle records must be objects')
    tombstones = {r[0] for r in db.execute('SELECT id FROM record_tombstones')}
    records = [validate_record(r) for r in raw if r.get('id') not in tombstones]
    if len({r['id'] for r in records}) != len(records):
        raise ValueError('duplicate record IDs')
    existing = {r[0] for r in db.execute("SELECT id FROM records WHERE kind='venue'")}
    existing.update(r['id'] for r in records if r['kind'] == 'venue')
    for r in records:
        if r['kind'] in {'product', 'promotion'} and r['attributes']['venue_id'] not in existing:
            raise ValueError(f"unknown venue_id in {r['id']}")
    for r in records:
        if missing_only and db.execute('SELECT 1 FROM records WHERE id=?', (r['id'],)).fetchone():
            continue
        upsert(db, r)
    return len(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path')
    args = parser.parse_args()
    with connect() as db:
        print(f'Loaded {load_bundle(db, args.path)} records')


if __name__ == '__main__':
    main()
