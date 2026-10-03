"""Typed evidence presentation and tenant schedules; no generated facts."""
from datetime import datetime, timedelta, time
from .context import BOLIVIA
from .store import parse_timestamp, tokens


def schedule_status(hours, now=None):
    now = (now or datetime.now(BOLIVIA)).astimezone(BOLIVIA)
    def intervals(day):
        return hours.get("special", {}).get(day.isoformat(), hours.get(str(day.weekday()), []))
    current = intervals(now.date())
    opened = False
    for day in (now.date() - timedelta(days=1), now.date()):
        for opens, closes in intervals(day):
            start = datetime.combine(day, time.fromisoformat(opens), BOLIVIA)
            end = datetime.combine(day, time.fromisoformat(closes), BOLIVIA)
            if end <= start:
                end += timedelta(days=1)
            opened |= start <= now < end
    return {"open_now": opened, "schedule_today": ", ".join("–".join(pair) for pair in current) or "cerrado"}


def matching_venues(db, query):
    """Only explicit tenant names count as a tenant-specific request."""
    from .store import search
    words = tokens(query)
    matches = []
    for record in search(db, query, limit=1000, kinds={'venue'}, browse=True):
        title = tokens(record["title"])
        aliases = []
        if {'almacen', 'pizzas'} <= title:
            aliases.append({'almacen'})
        if {'tuc', 'toys'} <= title:
            aliases.append({'tuc'})
        if {'cuarto', 'paseo'} <= title:
            aliases.append({'cuarto'})
        if {'chotto', 'matte'} <= title:
            aliases.append({'chotto'})
        if title and (title <= words or any(alias <= words for alias in aliases)):
            matches.append(record)
    return sorted(matches, key=lambda r: len(tokens(r["title"])), reverse=True)


def facts(record):
    a = record["attributes"]
    details = []
    if record["kind"] == "venue":
        details.append(f"Categoría: {a['category']}." if a.get("category") else "Negocio del directorio del Paseo.")
        if a.get("review_status") == "approved" and a.get("description"):
            details.append(a["description"])
        for label, field in (("Productos", "products"), ("Servicios", "services")):
            if a.get(field) and a.get("review_status") == "approved":
                details.append(f"{label}: {', '.join(a[field])}.")
    elif record["kind"] == "product":
        details.append(f"En {a.get('venue_name', a['venue_id'])}.")
        details.append(f"Precio: Bs {a['price_bs']:g}." if a.get("price_bs") is not None else "Consulta el precio.")
    elif record["kind"] == "promotion":
        details.extend([a["benefit"], f"Condiciones: {a['terms']}.",
                        f"Válida hasta {parse_timestamp(record['expires_at']).astimezone(BOLIVIA):%d/%m/%Y %H:%M}."])
    elif record["kind"] == "event":
        start = parse_timestamp(a["starts_at"]).astimezone(BOLIVIA)
        details.extend([f"{start:%d/%m/%Y %H:%M}, en {a['location']}.", a["description"]])
    elif record["kind"] == "faq":
        details.append(a.get("answer", "Consulta la fuente publicada para más detalles."))
    location = []
    for field, label in (("tower", "torre"), ("floor", "piso"), ("unit", "local"), ("area", "sector")):
        if a.get(field):
            value = str(a[field])
            if field == 'floor' and ('piso' in value.lower() or value.lower() == 'planta baja' or 'sótano' in value.lower()):
                location.append(value.lower())
            elif field == 'unit' and value.lower().startswith('oficina '):
                location.append(value)
            else:
                location.append(f"{label} {value}")
    if location:
        details.append("Ubicación: " + ", ".join(location) + ".")
    if a.get("reference") and a.get('data_origin') != 'synthetic_demo':
        details.append(f"Referencia: {a['reference']}.")
    return f"{record['title']}: " + " ".join(details)


def typed_answer(records, mode, message):
    if not records:
        return {"event_search": "No tengo eventos confirmados para esa fecha. Esto no significa que no haya actividades; falta una agenda vigente del Paseo.",
                "promotion_search": "No tengo promociones vigentes confirmadas. Puedo ayudarte a encontrar el negocio y consultar su fuente."}.get(mode)
    if mode == 'promotion_search':
        summaries = []
        for r in records[:3]:
            a = r['attributes']
            end = parse_timestamp(r['expires_at']).astimezone(BOLIVIA)
            month = ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')[end.month - 1]
            summaries.append(f"En {a.get('venue_name', 'el negocio')}: {a['terms']} Válida hasta el {end.day} de {month}.")
        return 'Te cuento las promociones que encontré: ' + ' '.join(summaries) + ' ¿Cuál te interesa?'
    if mode == 'event_search':
        return 'Puedes disfrutar de estas actividades: ' + ' '.join(facts(r) for r in records[:3]) + ' ¿Cuál te gustaría conocer mejor?'
    if records and all(r['kind'] == 'faq' for r in records):
        return ' '.join(r['attributes'].get('answer', '') for r in records[:3])
    if mode == 'product_search' and any(r['kind'] == 'product' for r in records):
        products = [r for r in records if r['kind'] == 'product'][:3]
        lines = [r['title'].split(' · ', 1)[0] + (f" por Bs {r['attributes']['price_bs']:g}" if r['attributes'].get('price_bs') is not None else '') +
                 f" en {r['attributes'].get('venue_name', 'la tienda')}" for r in products]
        return 'Te puedo mostrar ' + '; '.join(lines) + '. ¿Cuál te interesa?'
    answer = "Encontré estas opciones: " + " ".join(facts(r) for r in records[:3])
    words = tokens(message)
    if mode == "product_search" and all(r["kind"] != "product" for r in records):
        answer += " No tengo un catálogo con precio ni stock confirmados para esa consulta."
    if words & {"regalo", "recomiendas", "recomendacion"}:
        answer += " Estas opciones coinciden con lo que buscas. ¿Para quién es y qué presupuesto tienes?"
    if any(r['kind'] == 'venue' for r in records) and words & {'bs', 'bolivianos', 'presupuesto'}:
        answer += " El presupuesto no está confirmado para los negocios sin precios de catálogo."
    return answer
