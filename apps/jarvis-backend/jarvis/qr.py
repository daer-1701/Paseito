"""Generate destination QR images locally, without sending URLs to third parties."""
import os
from urllib.parse import quote, urlsplit

from .store import search


def destination_qr(db, record_id):
    record = next((r for r in search(db, '', limit=10000, browse=True) if r['id'] == record_id), None)
    if record is None:
        return None
    base = os.getenv('JARVIS_MOBILE_BASE_URL', '').rstrip('/')
    parsed = urlsplit(base)
    mobile = parsed.scheme in {'http', 'https'} and bool(parsed.netloc) and not parsed.query and not parsed.fragment and not parsed.username
    target = f'{base}/destination/{quote(record_id, safe="")}' if mobile else record.get('source_url', '')
    parsed = urlsplit(target or '')
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        return None
    import qrcode
    from qrcode.image.svg import SvgPathFillImage
    return qrcode.make(target, image_factory=SvgPathFillImage, border=4).to_string()
