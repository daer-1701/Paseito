"""Export existing venues as unpublished drafts for editorial review, not ingestion."""
import json
from .store import connect


def main():
    db = connect()
    try:
        records = []
        for row in db.execute("SELECT * FROM records WHERE kind='venue' ORDER BY title"):
            record = dict(row)
            record['attributes'] = json.loads(record['attributes'])
            record['attributes']['review_status'] = 'draft'
            record['attributes'].pop('verified_at', None)
            record['attributes'].pop('verified_by', None)
            records.append(record)
        print(json.dumps(records, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == '__main__':
    main()
