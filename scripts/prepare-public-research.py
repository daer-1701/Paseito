"""Compile the dated research bundle from a saved directory and existing venue IDs.

Does not access or modify the live database. The generated JSON is reviewed before
being applied with jarvis.import_records; unknown values and approvals stay absent.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/jarvis-backend'))
from jarvis.import_official import normalized, readable

STAMP = '2026-10-03T07:44:00-04:00'
DIRECTORY = 'https://paseoaranjuez.com/stores'
folder = ROOT / 'docs/entregables/investigacion-publica'
venues = json.loads((ROOT / 'docs/entregables/datos-paseo/negocios-para-revision.json').read_text(encoding='utf-8-sig'))
stores = json.loads((folder / 'directorio-oficial-2026-10-03.json').read_text(encoding='utf-8-sig'))
by_id = {r['id']: r for r in venues}
by_title = {normalized(r['title']): r['id'] for r in venues}
aliases = {'pauker': 'venue:opticas-pauker', 'sajama': 'venue:sajama-store',
           'tuctoystujugueteria': 'venue:tuc-toys'}
changed, unmatched, conflicts = {}, [], []

def patch(record_id, source, fields):
    record = changed.setdefault(record_id, json.loads(json.dumps(by_id[record_id])))
    attrs = record['attributes']
    attrs.update(fields)
    attrs.update(observed_at=STAMP, review_status='sourced', source_type='official_public_research')
    attrs.setdefault('field_sources', {}).update({key: source for key in fields})
    attrs.setdefault('source_urls', [])
    attrs['source_urls'] = list(dict.fromkeys([*attrs['source_urls'], record.get('source_url'), source]))
    attrs['source_urls'] = [u for u in attrs['source_urls'] if u]
    record['source_url'], record['updated_at'] = source, STAMP
    return record

for store in stores:
    title = readable(store['title'])
    key = normalized(title)
    record_id = by_title.get(key) or aliases.get(key)
    if not record_id:
        unmatched.append({'title': title, 'floor': readable(store.get('floor')), 'reason': 'identity needs review'})
        continue
    fields = {'directory_categories': [readable(c) for c in store.get('categories', [])],
              'public_contacts': store.get('social', {})}
    if store.get('link'):
        fields['menu_url'] = store['link']
    old_floor = by_id[record_id]['attributes'].get('floor')
    new_floor = readable(store.get('floor'))
    # Published directory confirms missing floors; curated floor numbers keep their format.
    if not old_floor and new_floor:
        fields['floor'] = new_floor
    patch(record_id, DIRECTORY, fields)

patch('venue:tuc-toys', 'https://toys.tuctuc.com.bo/contacto/', {'floor': '1', 'unit': '114'})
patch('venue:legend', 'https://www.impulse.bo/cms/page/view/page_id/7',
      {'floor': 'planta baja', 'unit': '6 y 3', 'reference': 'La marca publica planta baja, locales 6 y 3.'})
patch('venue:impulse', 'https://www.impulse.bo/cms/page/view/page_id/7', {'floor': '1', 'unit': '101-102'})
patch('venue:crocs', 'https://crocs.com.bo/nuestras-tiendas', {'floor': '2', 'unit': '13'})
patch('venue:lynx-samsung', 'https://samsung.com.bo/tiendas-samsung',
      {'floor': 'planta baja', 'unit': '9', 'reference': 'Samsung publica dos horarios diferentes para esta sucursal; confirmar el horario con LYNX.'})
conflicts.append({'id': 'venue:lynx-samsung', 'field': 'hours',
                 'published_values': ['Lunes a viernes 10:00–20:00', 'Lunes a domingo 10:00–21:00'],
                 'source': 'https://samsung.com.bo/tiendas-samsung', 'resolution': 'No schedule loaded; confirm with branch'})
patch('venue:opticas-pauker', 'https://opticaspauker.com/sucursales/',
      {'hours': {**{str(i): [['10:00', '22:00']] for i in range(6)}, '6': [['11:00', '21:00']]},
       'reference': 'Horario de la sucursal publicado por Pauker; sujeto a cambios y fechas especiales. Contacto público: +591 77000207.'})
# Sunday is not stated by Rezzom. Do not encode an omitted weekday as closed.
patch('venue:rezzom-beauty', 'https://www.rezzombeauty.com/',
      {'floor': '5', 'tower': '2', 'published_hours_text': 'Lunes a sábado 09:00–19:00, previa cita. Domingo y feriados sin publicar.',
       'reference': 'Lunes a sábado 09:00–19:00, previa cita. Domingo y feriados pendientes. Teléfono público: +591 75933553.'})
patch('venue:gool-store', 'https://linktr.ee/gool.store', {'floor': '2'})
patch('venue:el-cuarto', 'https://paseoaranjuez.com/', {'floor': '4',
      'reference': 'El Cuarto: lunes a jueves 12:00–23:00, viernes y sábado 12:00–01:00; domingos y feriados 12:00–22:00. Horario del área publicado por el Paseo.'})

services = []
for slug, title, category in (
    ('color', 'Mechas y color en Rezzom Beauty', 'servicio de peluquería color cabello'),
    ('corte', 'Corte y estilismo en Rezzom Beauty', 'servicio de peluquería corte peinado cabello'),
    ('manicura', 'Manicura y pedicura en Rezzom Beauty', 'servicio de belleza manos pies')):
    services.append({'id': f'product:rezzom-{slug}', 'kind': 'product', 'title': title, 'text': f'{title}. {category}. Atención previa cita.',
                     'attributes': {'venue_id': 'venue:rezzom-beauty', 'venue_name': 'Rezzom Beauty', 'category': category,
                                    'floor': '5', 'tower': '2', 'review_status': 'sourced', 'observed_at': STAMP,
                                    'reference': 'Servicio publicado por el negocio. Confirmar cita, costo y disponibilidad.'},
                     'source_url': 'https://www.rezzombeauty.com/', 'updated_at': STAMP})
events = [{'id': 'event:bingo-familiar-2026-10-04', 'kind': 'event', 'title': 'Bingo Familiar en El Club',
           'text': 'Bingo familiar domingo 4 de octubre de 2026, El Club Mercado Gastronómico, piso 3.',
           'source_url': 'https://paseoaranjuez.com/instagram/mercado_gastronomico_bypaseo/8', 'updated_at': STAMP,
           'attributes': {'starts_at': '2026-10-04T15:00:00-04:00', 'ends_at': '2026-10-04T18:00:00-04:00',
                          'location': 'El Club, Mercado Gastronómico, piso 3, Paseo Aranjuez',
                          'description': 'Actividad de bingo familiar anunciada en la agenda del Mercado Gastronómico.',
                          'floor': '3', 'review_status': 'sourced', 'observed_at': STAMP,
                          'original_publication': 'https://www.instagram.com/p/Dd4N9s0lRpi',
                          'source_type': 'official_site_public_feed'}}]
bundle = [*changed.values(), *services, *events]
(ROOT / 'apps/jarvis-backend/data/research-2026-10-03.json').write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
# Keep a new checkout's curated seed consistent with the dated research.
seed_path = ROOT / 'apps/jarvis-backend/data/venues.json'
seed = json.loads(seed_path.read_text(encoding='utf-8'))
seed = [changed.get(r['id'], r) for r in seed]
seed_path.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
summary = {'observed_at': STAMP, 'directory_entries': len(stores), 'enriched_venues': len(changed), 'new_services': len(services), 'new_events': len(events),
           'unmatched_directory_entries': unmatched, 'conflicts': conflicts,
           'note': 'Public sources only; no human approvals, branch stock or active promotions inferred.'}
(folder / 'resumen-carga.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
