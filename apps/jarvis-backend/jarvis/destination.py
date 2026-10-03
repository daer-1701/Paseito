"""Public, session-free destination page for continuing on a phone."""
from html import escape
import os
from .store import search
from .knowledge import facts


def destination_page(db, record_id):
    record = next((r for r in search(db, '', limit=10000, browse=True) if r['id'] == record_id), None)
    if not record:
        return None
    if record['kind'] == 'product':
        from .conversation import catalog_prices
        record = catalog_prices(db, [record])[0]
    a = record['attributes']
    title = escape(record['title'])
    description = escape(facts(record))
    date = escape(a.get('verified_at') or a.get('observed_at') or 'Fecha de revisión pendiente')
    url = escape(record['source_url'], quote=True)
    demo = '<p><a href="/catalog/demo">Modo demo</a></p>' if os.getenv('JARVIS_DEMO_CATALOG') == '1' else ''
    return f'''<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · Paseo Aranjuez</title>
<style>body{{font:18px/1.6 system-ui;background:#faf7f0;color:#302329;margin:0;padding:28px}}main{{max-width:650px;margin:auto}}h1{{line-height:1.15}}a{{color:#852044}}footer{{margin-top:32px;font-size:15px}}button{{font:inherit;padding:12px}}</style>
<main>{demo}<p>Paseo Aranjuez · Ubicación publicada</p><h1>{title}</h1><p>{description}</p>
<p>No hay un recorrido interior validado para esta ficha. Confirma accesos y rutas accesibles con atención del Paseo.</p>
<p><a href="{url}" rel="noopener noreferrer">Consultar fuente publicada</a></p>
<button onclick="window.print()">Guardar o imprimir</button><footer>Fecha de fuente: {date}. Esta página no contiene el historial de tu conversación.</footer></main></html>'''
