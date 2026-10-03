"""Small shopping dialogue: prepare a query, offer shops, then show their catalogue."""
import re
import unicodedata
from .store import search, tokens
from .knowledge import matching_venues


ALIASES = {
    'camisas': 'camisa', 'poleras': 'polera', 'remeras': 'polera', 'remera': 'polera',
    'zapatos': 'zapato', 'zapatilla': 'zapatillas', 'tenis': 'zapatillas',
    'pizzas': 'pizza', 'cafecito': 'cafe', 'cafes': 'cafe', 'juguete': 'juguetes',
    'pantalones': 'pantalon', 'vestidos': 'vestido', 'perfumes': 'perfume',
    'hamburguesas': 'hamburguesa', 'celulares': 'celular', 'mochilas': 'mochila',
    'helados': 'helado', 'accesorio': 'accesorios', 'comer': 'comida',
    'hambre': 'comida', 'almorzar': 'comida', 'cenar': 'comida',
}
NOISE = {'busco', 'buscar', 'gustaria', 'favor', 'hola', 'buenas', 'tardes', 'dias',
         'tienes', 'tienen', 'tenemos', 'muestre', 'muestrame', 'mostrar', 'muestra',
         'ver', 'dame', 'ensename', 'ensena', 'catalogo', 'catalogos', 'producto',
         'productos', 'precio', 'precios', 'cuesta', 'cuestan', 'cuanto', 'stock',
         'disponible', 'disponibles', 'disponibilidad', 'comprar', 'tienda', 'tiendas',
         'presupuesto', 'hasta', 'menos', 'maximo', 'max', 'bolivianos', 'bs', 'tengo',
         'gastar', 'una', 'uno', 'ese', 'esa', 'ahi', 'primera', 'primero', 'segunda',
         'segundo', 'tercera', 'tercero', 'mas', 'otras', 'otros', 'opciones'}
TOPICS = {
    'camisa', 'polera', 'ropa', 'zapato', 'zapatillas', 'juguetes', 'infantil',
    'pizza', 'cafe', 'comida', 'hamburguesa', 'pasta', 'helado', 'postre', 'waffle',
    'mochila', 'pantalon', 'vestido', 'perfume', 'accesorios', 'celular', 'tecnologia',
    'maquillaje', 'labial', 'joyas', 'flores', 'medias', 'calzado', 'bata', 'reloj',
    'corte', 'manicura', 'pedicura', 'gafas', 'regalo', 'cargador', 'auriculares',
}
FOOD = {'pizza', 'hamburguesa', 'cafe', 'postres', 'pasta', 'mexicana', 'japonesa',
        'criolla', 'bar', 'espanola', 'turca'}


def normalize(message):
    text = ''.join(c for c in unicodedata.normalize('NFD', message.lower())
                   if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', text).strip()


def prepare(message):
    words = tokens(message)
    useful = {ALIASES.get(w, w) for w in words - NOISE if not w.isdigit()}
    return useful, ' '.join(sorted(useful))


def product_name(record):
    return record['title'].split(' · ', 1)[0]


def readable_list(items):
    if len(items) < 2:
        return ''.join(items)
    return ', '.join(items[:-1]) + ' y ' + items[-1]


def catalog_prices(db, products, budget=None):
    promotions = search(db, '', kinds={'promotion'}, browse=True, limit=10000)
    offers = {}
    for promo in promotions:
        a = promo['attributes']
        if a.get('product_id') and a.get('price_bs') is not None:
            previous = offers.get(a['product_id'])
            if previous is None or a['price_bs'] < previous['attributes']['price_bs']:
                offers[a['product_id']] = promo
    result = []
    for product in products:
        promo = offers.get(product['id'])
        if promo and promo['attributes']['venue_id'] == product['attributes'].get('venue_id'):
            attrs = product['attributes']
            if attrs.get('price_bs') is None or promo['attributes']['price_bs'] < attrs['price_bs']:
                product = {**product, 'attributes': {**attrs, 'catalog_price_bs': attrs.get('price_bs'),
                            'price_bs': promo['attributes']['price_bs'], 'active_promotion': promo['attributes']['benefit'],
                            'promotion_id': promo['id'], 'promotion_expires_at': promo['expires_at']}}
                product['text'] = product['title'] + f". Precio vigente: Bs {promo['attributes']['price_bs']:g}. " + promo['attributes']['terms']
        if budget is None or product['attributes'].get('price_bs') is not None and product['attributes']['price_bs'] <= budget:
            result.append(product)
    return result


def response(answer, sources=(), stage='shops', suggestions=()):
    return {'intent': 'product_search' if stage == 'catalog' else 'discovery',
            'answer': answer, 'sources': list(sources), 'suggestions': list(suggestions),
            'grounded': True, 'answer_mode': 'strict', 'dialogue_stage': stage,
            'contains_demo_data': any(r['attributes'].get('data_origin') == 'synthetic_demo'
                                      for r in sources)}


def shopping_dialogue(db, message, mode, preferences, previous_ids):
    if mode not in {'discovery', 'product_search'}:
        return None
    raw = normalize(message)
    words = tokens(message)
    useful, prepared = prepare(message)
    venues = search(db, '', kinds={'venue'}, browse=True, limit=10000)
    by_id = {r['id']: r for r in venues}
    explicit = matching_venues(db, message)
    selected = explicit[0]['id'] if explicit else None
    offered = [v for v in preferences.get('offered_venues', []) if v in by_id]
    ordinal = None
    for index, forms in enumerate(({'primera', 'primero', '1'}, {'segunda', 'segundo', '2'}, {'tercera', 'tercero', '3'})):
        if set(re.findall(r'\w+', raw)) & forms:
            ordinal = index
    if not selected and ordinal is not None and ordinal < len(offered):
        selected = offered[ordinal]
    requests_catalog = bool(words & {'catalogo', 'catalogos', 'productos', 'precios', 'muestrame', 'ensename'})
    inventory_query = bool(words & {'stock', 'disponibilidad', 'disponible', 'disponibles', 'talla', 'tallas', 'colores', 'color'})
    follow = requests_catalog or bool(words & {'ahi', 'esa', 'ese', 'cuesta', 'precio', 'stock', 'disponibilidad', 'disponible', 'mas', 'otras', 'otros', 'siguientes'})
    if not selected and (follow or raw in {'si', 'claro', 'dale'}) and preferences.get('selected_venue') in by_id:
        selected = preferences['selected_venue']
    if not selected and follow and len(offered) == 1:
        selected = offered[0]

    # Do not intercept greetings, public FAQs or unrelated unsupported questions.
    if not selected and not (useful & TOPICS) and not requests_catalog and ordinal is None and not inventory_query:
        if preferences.get('shop_topic') and (words & {'nino', 'nina', 'pareja', 'infantil', 'presupuesto', 'bolivianos', 'bs'} or raw.replace('.', '').replace(',', '').isdigit() and preferences.get('budget_bs') is not None):
            useful, prepared = prepare(preferences['shop_topic'])
        elif raw in {'hola', 'buenas', 'buenos dias', 'buenas tardes', 'buenas noches'}:
            return response('¡Hola! Soy Paseito. ¿Buscas una tienda, algo para comer o un regalo?', stage='welcome')
        else:
            return None
    if inventory_query:
        return response('Puedo mostrarte productos y precios del catálogo, pero todavía no consulto existencias en tiempo real. ¿Qué tienda o producto quieres ver?',
                        [by_id[selected]] if selected else [], stage='inventory_pending')
    catalog_ids = preferences.get('catalog_ids', previous_ids)
    if not explicit and preferences.get('dialogue_stage') == 'catalog' and ordinal is not None and ordinal < len(catalog_ids):
        available = catalog_prices(db, search(db, '', kinds={'product'}, browse=True, limit=10000))
        product = next((r for r in available if r['id'] == catalog_ids[ordinal]), None)
        if product:
            price = product['attributes'].get('price_bs')
            text = f"La opción que elegiste es {product_name(product)}"
            if price is not None:
                text += f" por Bs {price:g}"
            text += '. ¿Quieres ver más opciones o consultar el horario de la tienda?'
            return response(text, [product], 'catalog')

    if useful & {'regalo'}:
        if preferences.get('recipient') == 'infantil' or words & {'nino', 'nina', 'bebe'}:
            useful, prepared = {'juguetes'}, 'juguetes'
        elif words & {'pareja', 'mama', 'papa', 'amiga', 'amigo'}:
            useful, prepared = {'accesorios'}, 'accesorios'
        else:
            preferences['shop_topic'] = message
            return response('Claro, te ayudo a elegir un regalo. ¿Para quién es y cuánto te gustaría gastar? Podemos empezar por ropa, juguetes o accesorios.',
                            stage='clarify', suggestions=['Un regalo para un niño', 'Busco ropa', 'Busco accesorios'])

    budget = preferences.get('budget_bs')
    if selected:
        venue = by_id[selected]
        # The choice can be a short name/ordinal. Preserve the preceding product topic.
        venue_words = tokens(venue['title'])
        specific = useful - venue_words
        if not specific or not (specific & TOPICS):
            specific, _ = prepare(preferences.get('shop_topic', ''))
        show_all = requests_catalog or not specific
        query = '' if show_all else ' '.join(sorted(specific))
        more = bool(words & {'mas', 'otras', 'otros', 'siguientes'}) and selected == preferences.get('selected_venue')
        if more:
            query = preferences.get('catalog_query', query)
            specific = tokens(query)
            show_all = not query
        products = catalog_prices(db, search(db, query, kinds={'product'}, browse=show_all, venue_ids={selected},
                          limit=10000), budget)
        # Expanded category matches are useful for finding shops, not for a precise catalogue.
        exact = [r for r in products if specific & tokens(product_name(r))]
        if exact and not show_all:
            products = exact
        page = preferences.get('catalog_page', 0) + 1 if more else 0
        preferences.update(selected_venue=selected, catalog_page=page, catalog_query=query, offered_venues=[selected])
        start = page * 5
        shown = products[start:start + 5]
        preferences['catalog_ids'] = [r['id'] for r in shown]
        if not shown:
            text = ('Ya te mostré todas las opciones de esta búsqueda. Puedes pedirme otro producto o cambiar de tienda.'
                    if products else f'No encontré productos de {venue["title"]} que coincidan con esa búsqueda' +
                    (f' por hasta Bs {budget:g}.' if budget is not None else '.'))
            return response(text, [venue], 'catalog', ['Ver catálogo de ' + venue['title']])
        lines = [product_name(r) + (f" por Bs {r['attributes']['price_bs']:g}" if r['attributes'].get('price_bs') is not None else '') for r in shown]
        answer = f'Te muestro {len(shown)} opciones de {venue["title"]}: ' + '; '.join(lines) + '. '
        answer += '¿Cuál te interesa?' if start + len(shown) >= len(products) else '¿Cuál te interesa? También puedes pedirme más opciones.'
        preferences['shop_topic'] = preferences.get('shop_topic') or message
        next_option = 'Más opciones' if start + len(shown) < len(products) else 'Ver catálogo de ' + venue['title']
        return response(answer, shown, 'catalog', [next_option, 'Horario de ' + venue['title']])

    if requests_catalog and offered:
        return response('¿De cuál tienda quieres ver el catálogo: ' + readable_list([by_id[v]['title'] for v in offered]) + '?',
                        [by_id[v] for v in offered], suggestions=[by_id[v]['title'] for v in offered])
    if not prepared:
        return response('¿Qué te gustaría encontrar: ropa, juguetes, comida o tecnología?', stage='clarify')
    products = catalog_prices(db, search(db, prepared, kinds={'product'}, limit=10000), budget)
    if 'comida' in useful:
        products = [r for r in catalog_prices(db, search(db, '', kinds={'product'}, browse=True, limit=10000), budget)
                    if r['attributes'].get('category') in FOOD]
    else:
        exact = [r for r in products if useful & tokens(product_name(r))]
        if exact:
            products = exact
    excluded = set()
    for match in re.finditer(r'\b(?:sin|no quiero|excepto)\s+(\w+)', raw):
        excluded.add(ALIASES.get(match.group(1), match.group(1)))
    products = [r for r in products if not excluded & tokens(product_name(r))]
    if words & {'vegano', 'vegana', 'alergia', 'mani', 'gluten'}:
        return response('Puedo ayudarte a encontrar restaurantes, pero necesito información de sus ingredientes para recomendarte algo con esas restricciones. ¿Quieres ver opciones y consultarles directamente?', stage='clarify')
    grouped = {}
    for product in products:
        vid = product['attributes'].get('venue_id')
        if vid in by_id:
            grouped.setdefault(vid, []).append(product)
    chosen = list(grouped)[:3]
    if not chosen:
        return response('No encontré una opción que coincida' + (f' por hasta Bs {budget:g}' if budget is not None else '') + '. ¿Probamos otro producto o cambiamos el presupuesto?', stage='clarify')
    preferences.update(offered_venues=chosen, shop_topic=prepared, catalog_page=0)
    preferences.pop('selected_venue', None)
    summaries = [f"{by_id[vid]['title']}, donde puedes encontrar {readable_list(list(dict.fromkeys(product_name(r).lower() for r in grouped[vid]))[:2])}"
                 for vid in chosen]
    examples = [list(dict.fromkeys(product_name(r).lower() for r in grouped[vid]))[:2] for vid in chosen]
    amount = 'estas tres tiendas' if len(chosen) == 3 else 'estas dos tiendas' if len(chosen) == 2 else 'esta opción'
    if len(chosen) > 1 and all(example == examples[0] for example in examples):
        answer = f'Te comento que tenemos {amount}: ' + readable_list([by_id[vid]['title'] for vid in chosen]) + '. En ellas puedes encontrar ' + readable_list(examples[0]) + '. '
    else:
        answer = f'Te comento que tenemos {amount}: ' + '; '.join(summaries) + '. '
    if budget is not None:
        answer += f'Encontré opciones dentro de tus Bs {budget:g}. '
    answer += '¿Cuál te gusta más para que te muestre su catálogo?'
    return response(answer, [by_id[v] for v in chosen], suggestions=[by_id[v]['title'] for v in chosen])
