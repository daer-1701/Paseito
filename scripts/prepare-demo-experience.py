"""Author schedules and promotions for the explicitly opt-in presentation dataset."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
coverage = json.loads((ROOT / 'docs/entregables/catalogo-demo-cobertura.json').read_text(encoding='utf-8'))
food = {'pizza', 'hamburguesa', 'cafe', 'postres', 'pasta', 'mexicana', 'japonesa', 'criolla', 'bar', 'espanola', 'turca'}
hours = {}
for venue in coverage:
    profile = venue.get('profile')
    week = {}
    for day in range(7):
        interval = ['11:00', '20:00'] if day == 6 else ['10:00', '21:00']
        if profile in food:
            interval = ['11:00', '23:00'] if day in (4, 5) else ['11:00', '22:00']
        if profile == 'cafe':
            interval = ['09:00', '21:00'] if day == 6 else ['08:30', '21:30']
        if profile == 'salon':
            interval = ['10:00', '17:00'] if day == 6 else ['09:00', '19:00']
        if venue['title'] == 'El Cuarto by Paseo':
            interval = ['17:00', '02:00'] if day in (4, 5) else ['13:00', '23:00'] if day == 6 else ['17:00', '00:00']
        if venue['count'] == 0:
            week[str(day)] = [] if day == 6 else [['09:00', '13:00']] if day == 5 else [['09:00', '18:00']]
        else:
            week[str(day)] = [interval]
    hours[venue['venue_id']] = week

by_title = {v['title']: v['venue_id'] for v in coverage}
stamp = datetime.now(timezone.utc).isoformat()
start = '2026-10-03T00:00:00-04:00'
end = '2026-10-11T23:59:00-04:00'
offers = [
    ('Almacén de Pizzas', 'Pizza familiar de 8 porciones por Bs 59', 'Una pizza familiar de 8 porciones por Bs 59. Sabores margarita o pepperoni; consumo en local. No acumulable con otros descuentos.', 59),
    ('Bypass Burger', 'Combo clásico por Bs 39', 'Hamburguesa clásica, papas pequeñas y gaseosa por Bs 39. Consumo en local; una bebida por combo.', 39),
    ('Pawitos', 'Café y brownie por Bs 29', 'Café americano y brownie por Bs 29, de 15:00 a 18:00. Una porción por combo; consumo en local.', 29),
    ('Solo Pastas', 'Dos pastas por Bs 79', 'Dos pastas boloñesa o Alfredo por Bs 79; consumo en local. No incluye bebidas.', 79),
    ('Helados Vacafría', 'Dos helados por Bs 25', 'Dos helados de una porción por Bs 25. No incluye toppings; consumo en local.', 25),
    ('TUC TOYS', 'Rompecabezas y cubo por Bs 69', 'Rompecabezas infantil y cubo Rubik por Bs 69. Un set por compra; modelos del catálogo.', 69),
    ('Gap', 'Pack de dos poleras por Bs 129', 'Dos poleras básicas por Bs 129. No acumulable con otros descuentos; no incluye prendas estampadas.', 129),
    ('Totto', 'Mochila urbana por Bs 199', 'Mochila urbana del catálogo por Bs 199. No incluye mochilas para laptop ni maletas.', 199),
]
records = []
for index, (title, benefit, terms, price) in enumerate(offers, 1):
    product_id = (f"product:demo:{by_title[title].removeprefix('venue:')}:05" if title == 'Almacén de Pizzas' else
                  f"product:demo:{by_title[title].removeprefix('venue:')}:01" if title == 'Totto' else None)
    records.append({'id': f'promotion:demo:2026-10:{index:02}', 'kind': 'promotion',
                    'title': f'{benefit} · {title}', 'text': f'{benefit}. Promoción en {title}. {terms}',
                    'source_url': 'http://localhost:8000/catalog/demo', 'updated_at': stamp,
                    'expires_at': end, 'attributes': {'venue_id': by_title[title], 'venue_name': title,
                        'starts_at': start, 'benefit': benefit, 'terms': terms, 'price_bs': price, 'product_id': product_id,
                        'data_origin': 'synthetic_demo', 'source_type': 'demo_promotion', 'review_status': 'sourced'}})
(ROOT / 'apps/jarvis-backend/data/demo-schedules.json').write_text(json.dumps(hours, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(ROOT / 'apps/jarvis-backend/data/demo-promotions.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'schedules': len(hours), 'promotions': len(records), 'valid_until': end}))
