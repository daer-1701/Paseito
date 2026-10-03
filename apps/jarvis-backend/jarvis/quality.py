"""Administrative coverage report: observation never implies approval."""
import json
from datetime import datetime, timezone
from .store import parse_timestamp


def report(db):
    now = datetime.now(timezone.utc)
    counts, issues = {}, []
    for row in db.execute('SELECT * FROM records ORDER BY kind, title'):
        a = json.loads(row['attributes'])
        counts[row['kind']] = counts.get(row['kind'], 0) + 1
        missing = []
        if row['kind'] == 'venue':
            missing.extend(key for key in ('floor', 'unit', 'hours') if not a.get(key))
        if row['kind'] == 'product':
            missing.extend(key for key in ('price_bs', 'stock') if a.get(key) is None)
        if a.get('review_status') != 'approved':
            missing.append('human_review')
        if not a.get('observed_at') and not a.get('verified_at'):
            missing.append('source_date')
        if row['expires_at'] and parse_timestamp(row['expires_at']) <= now:
            missing.append('expired')
        if missing:
            issues.append({'id': row['id'], 'title': row['title'], 'kind': row['kind'], 'missing': missing})
    return {'counts': counts, 'issues': issues, 'generated_at': now.isoformat(),
            'note': 'Los campos ausentes requieren confirmación; no deben inferirse.'}


if __name__ == '__main__':
    from contextlib import closing
    from .store import connect
    with closing(connect()) as db:
        print(json.dumps(report(db), ensure_ascii=False, indent=2))
