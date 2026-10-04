"""Grounded conversational response with optional OpenAI synthesis."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .context import opening_status
from .store import search
from .weather import current_weather
from .knowledge import matching_venues, schedule_status, typed_answer
from .context import BOLIVIA
from .store import tokens
from .conversation import shopping_dialogue, catalog_prices
from .orientation import location_text
import re


FALLBACK = "No tengo información confirmada para responder eso. Puedo ayudarte a buscar negocios, productos, promociones o eventos del Paseo."
STRICT_RESPONSE_MODE = "strict"


def intent(message: str) -> str:
    from .store import tokens
    import unicodedata
    raw=''.join(c for c in unicodedata.normalize('NFKD',message.lower()) if not unicodedata.combining(c))
    words = tokens(message)
    if words & {"puntos", "saldo", "recompensa", "recompensas", "canje"}:
        return "loyalty"
    if words & {"pedido", "orden", "retiro", "reserva", "reservar", "reservame", "pagar", "paga", "compra", "comprame", "canjear", "cancelar", "cancelacion", "devolucion", "devolver", "pago", "pagos", "recoger", "recogerlo", "recogerla", "recogerlos", "recogerlas", "reservas", "reservacion", "reservaciones"}:
        return "order"
    if (words & {"guiame", "guia", "llegar", "llego", "ruta", "direccion", "direcciones", "ubicacion", "ubicado", "ubicada", "queda", "quedan"}
            or re.search(r'\bdonde\s+(?:esta|estan|se encuentra|se encuentran|queda|quedan)\b',raw)):
        return "navigation"
    if words & {"clima", "tiempo", "lluvia", "llueve", "temperatura"}:
        return "weather"
    if words & {"abierto", "abierta", "abiertos", "abiertas", "cerrado", "cerrada", "horario", "horarios", "abre", "abren", "cierra", "cierran"}:
        return "hours"
    if words & {"promocion", "promociones", "descuento", "descuentos", "oferta", "ofertas"}:
        return "promotion_search"
    if words & {"evento", "eventos", "actividad", "actividades", "concierto", "feria", "agenda"}:
        return "event_search"
    if words & {"describe", "descripcion", "describeme"}:
        return "venue_info"
    if words & {"producto", "productos", "comprar", "precio", "cuesta", "cuestan", "stock", "disponibilidad", "servicio", "servicios"}:
        return "product_search"
    return "discovery"


def local_answer(records: list[dict]) -> str:
    return typed_answer(records, "discovery", "") or FALLBACK


def operation_answer(message: str) -> str:
    words=tokens(message)
    if words & {'cancelar','cancelacion','devolucion','devolver'}:
        return 'Para cancelar o solicitar una devolución, contacta al comercio o usa la plataforma donde hiciste la compra o reserva. Puedo ayudarte a encontrar el negocio y su información.'
    if words & {'reserva','reservar','reservame','reservas','reservacion','reservaciones'}:
        return 'Las reservas se confirman directamente con el negocio. Puedo mostrarte opciones, horarios y ubicación; aquí todavía no consulto disponibilidad de mesas o salas ni registro reservas.'
    if words & {'pagar','paga','pago','pagos'}:
        return 'El pago se realiza con el comercio o desde su plataforma de compra. Aquí puedo ayudarte a revisar productos, precios y ubicación.'
    if words & {'retiro','recoger','recogerlo','recogerla','recogerlos','recogerlas'}:
        return 'El comercio o PaseoYa deben confirmar el estado y horario de retiro de tu pedido. Aquí puedo ayudarte a ubicar el negocio, pero todavía no consulto pedidos ni valido entregas.'
    return 'La creación y el seguimiento de pedidos requieren la integración con PaseoYa. Por ahora puedo ayudarte a elegir productos y encontrar el negocio; aquí no se confirma ninguna compra.'


def navigation_answer(record: dict | None) -> str:
    if not record:
        return FALLBACK
    attrs = record["attributes"]
    floor = attrs.get("floor")
    unit = attrs.get("unit")
    if not floor:
        return f"Encontré {record['title']}, pero no tengo un piso confirmado para guiarte."
    return (f"Te ubico: {record['title']} está en {location_text(attrs)}. "
            "En la torre de la pantalla te señalo su piso; puedes llevarte la ficha al teléfono con el QR. "
            "Para el recorrido desde tu posición, consulta la señalización del Paseo.")


def chat(db, message: str, session_id: str | None = None,
         records_override: list[dict] | None = None, allow_external: bool = True) -> dict:
    if not isinstance(message, str) or not message.strip() or len(message) > 2000:
        raise ValueError("message must contain 1 to 2000 characters")
    session_id = session_id or str(uuid4())
    if not isinstance(session_id, str) or len(session_id) > 100:
        raise ValueError("invalid session_id")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    db.execute('DELETE FROM turns WHERE created_at < ?', (cutoff,))
    db.execute('DELETE FROM session_context WHERE updated_at < ?', (cutoff,))
    db.execute('DELETE FROM session_preferences WHERE updated_at < ?', (cutoff,))
    history = [dict(row) for row in db.execute(
        "SELECT role, content FROM turns WHERE session_id=? ORDER BY id DESC LIMIT 4", (session_id,))]
    history.reverse()
    previous_user = next((item["content"] for item in reversed(history) if item["role"] == "user"), "")
    saved = db.execute("SELECT record_ids FROM session_context WHERE session_id=?", (session_id,)).fetchone()
    previous_ids = json.loads(saved[0]) if saved else []
    pref_row = db.execute('SELECT preferences FROM session_preferences WHERE session_id=?', (session_id,)).fetchone()
    preferences = json.loads(pref_row[0]) if pref_row else {}
    budget_match = re.search(r"(?:bs\.?\s*(\d+(?:[.,]\d+)?)|(\d+(?:[.,]\d+)?)\s*(?:bs|bolivianos))", message, re.I)
    remaining = {w for w in tokens(message) if not w.isdigit()} - {'hasta', 'menos', 'maximo', 'max', 'presupuesto', 'bolivianos', 'tengo', 'gastar', 'bs'}
    preference_reply = bool((budget_match and not remaining) or re.match(r'^para (?:mi|un|una|el|la)\b', message.lower().strip())) and bool(preferences.get('topic'))
    if budget_match:
        preferences['budget_bs'] = float((budget_match.group(1) or budget_match.group(2)).replace(',', '.'))
    elif preferences.get('dialogue_stage') == 'clarify' and re.fullmatch(r'\s*\d+(?:[.,]\d+)?\s*', message):
        preferences['budget_bs'] = float(message.strip().replace(',', '.'))
    if tokens(message) & {'nino', 'nina', 'ninos', 'bebe'}:
        preferences['recipient'] = 'infantil'
    mode = intent(message)
    choice = re.fullmatch(r'\s*(?:la |el |esa |ese )?(primera|primero|segunda|segundo|tercera|tercero|[123])\s*[.!?]?\s*',message.lower())
    if choice and previous_ids:
        index = 1 if choice[1] in {'segunda','segundo','2'} else 2 if choice[1] in {'tercera','tercero','3'} else 0
        selected_id = previous_ids[min(index,len(previous_ids)-1)]
        available = search(db,'',browse=True,limit=10000)
        selected = next((r for r in available if r['id']==selected_id),None)
        if selected and selected['kind'] in {'event','promotion'}:
            mode = 'event_search' if selected['kind']=='event' else 'promotion_search'
            records_override = [selected]
        elif selected and selected['kind']=='product':
            mode = 'product_search'
            records_override = catalog_prices(db,[selected],preferences.get('budget_bs'))
            preferences['selected_venue'] = selected['attributes']['venue_id']
            preferences['catalog_ids'] = [selected_id]
            preferences['dialogue_stage'] = 'catalog'
        elif selected and selected['kind']=='venue':
            preferences['offered_venues'] = [r_id for r_id in previous_ids if any(r['id']==r_id and r['kind']=='venue' for r in available)]
    if mode == 'discovery' and preferences.get('selected_venue') and tokens(message) & {'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'}:
        mode = 'hours'
    if mode in {'discovery', 'promotion_search'} and previous_ids and tokens(message) & {'condiciones', 'incluye', 'vigencia', 'vence', 'cuando', 'esa', 'ese', 'interesa'}:
        previous_promos = [r for r in search(db, '', kinds={'promotion'}, browse=True, limit=10000) if r['id'] in previous_ids]
        if previous_promos and not matching_venues(db, message):
            mode = 'promotion_search'
            records_override = previous_promos
    shop_result = shopping_dialogue(db, message, mode, preferences, previous_ids) if records_override is None else None
    if shop_result is not None:
        result = {'session_id': session_id, **shop_result}
    elif mode == "loyalty":
        result = {"session_id": session_id, "intent": mode,
                "answer": "Para consultar tus puntos necesito conectarme a Paseo Points con tu sesión autenticada. Esa información no se guarda en la búsqueda pública.",
                "sources": [], "suggestions": [], "grounded": True, "answer_mode": STRICT_RESPONSE_MODE}
    elif mode == "order":
        result = {"session_id": session_id, "intent": mode,
                "answer": operation_answer(message),
                "sources": [], "suggestions": [], "grounded": True, "answer_mode": STRICT_RESPONSE_MODE}
    elif mode == "hours":
        venues = matching_venues(db, message)
        if not venues and preferences.get('selected_venue'):
            venues = [r for r in search(db, '', kinds={'venue'}, browse=True, limit=10000)
                      if r['id'] == preferences['selected_venue']]
        if not venues and tokens(message) & {"ahi", "ese", "esa", "abre", "cierra"}:
            venues = matching_venues(db, previous_user)
            if not venues and previous_ids:
                available = search(db, '', kinds={'venue'}, limit=1000, browse=True)
                venues = [r for r in available if r['id'] == previous_ids[0]]
        if venues:
            venue = venues[0]
            if venue['attributes'].get('hours'):
                status = schedule_status(venue['attributes']['hours'])
                venue['attributes'].update(status)
                day = next((n for n, name in enumerate(('lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo')) if name in tokens(message)), None)
                if day is not None:
                    intervals = venue['attributes']['hours'].get(str(day), [])
                    schedule = ', '.join('–'.join(pair) for pair in intervals) or 'cerrado'
                    name = ('lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo')[day]
                    text = f"El {name}, {venue['title']} atiende de {schedule}." if intervals else f"{venue['title']} no abre el {name}."
                else:
                    schedule = status['schedule_today']
                    text = f"{venue['title']} {'está abierto' if status['open_now'] else 'está cerrado'} ahora. " + (f"Hoy atiende de {schedule} (hora de Cochabamba)." if schedule != 'cerrado' else 'Hoy no tiene atención programada.')
                context = {"answer": text, "sources": [venue]}
            elif venue['attributes'].get('published_hours_text'):
                context = {"answer": f"Horario publicado de {venue['title']}: {venue['attributes']['published_hours_text']} No puedo confirmar apertura actual ni excepciones con esta información parcial.", "sources": [venue]}
            else:
                context = {"answer": f"No tengo el horario individual confirmado de {venue['title']}. " + opening_status()['answer'], "sources": opening_status()['sources']}
        else:
            if tokens(message) & {'tienda', 'tiendas', 'negocios', 'locales', 'abierto', 'abierta', 'abiertos', 'abiertas'}:
                venues = search(db, '', kinds={'venue'}, browse=True, limit=10000)
                opened = []
                for venue in venues:
                    if venue['attributes'].get('hours'):
                        status = schedule_status(venue['attributes']['hours'])
                        if status['open_now']:
                            venue['attributes'].update(status)
                            opened.append(venue)
                context = {'answer': ('Ahora puedes visitar ' + ', '.join(r['title'] for r in opened[:5]) + '. ¿Qué te gustaría encontrar?' if opened else 'Ahora no encuentro negocios abiertos según los horarios disponibles. ¿De qué tienda quieres consultar el horario?'), 'sources': opened[:5]}
            else:
                context = opening_status()
        result = {"session_id": session_id, "intent": mode, **context, "suggestions": [],
                  "grounded": True, "answer_mode": STRICT_RESPONSE_MODE}
    elif mode == "weather":
        try:
            if not allow_external:
                raise RuntimeError('live weather is unavailable in the presentation channel')
            context = current_weather()
            result = {"session_id": session_id, "intent": mode, **context, "suggestions": [],
                      "grounded": True, "answer_mode": STRICT_RESPONSE_MODE}
        except RuntimeError:
            result = {"session_id": session_id, "intent": mode,
                      "answer": "No puedo confirmar el clima actual en este momento.", "sources": [],
                      "suggestions": [], "grounded": True, "answer_mode": STRICT_RESPONSE_MODE}
    else:
        # Short follow-up questions reuse the user's preceding topic.
        follow_up = bool(tokens(message) & {"ahi", "queda", "ese", "esa", "primero", "primera", "segundo", "segunda"})
        query = message + (" " + previous_user if previous_user and follow_up else "")
        if preference_reply:
            query += ' ' + preferences['topic']
        if preferences.get('recipient') == 'infantil' and ('regalo' in tokens(query)):
            query += ' juguetes infantil'
        kinds = {"event_search": {"event"}, "promotion_search": {"promotion"},
                 "navigation": {"venue", "faq"}, "venue_info": {"venue"}, "product_search": {"product"}}.get(mode, {"venue", "faq", "product"})
        event_day = None
        now = datetime.now(BOLIVIA)
        if mode == "event_search":
            if "hoy" in tokens(message):
                event_day = now.date()
            elif "manana" in tokens(message):
                event_day = now.date() + timedelta(days=1)
            else:
                date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", message)
                if date_match:
                    try:
                        event_day = datetime.fromisoformat(date_match.group()).date()
                    except ValueError:
                        return {"session_id": session_id, "intent": mode, "answer": "Esa fecha no es válida. Usa AAAA-MM-DD.", "sources": [], "suggestions": [], "grounded": True, "answer_mode": STRICT_RESPONSE_MODE}
        topic = tokens(re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "", query)) - {
            "evento", "eventos", "actividad", "actividades", "agenda", "hoy", "manana", "proximos", "proximo",
            "promocion", "promociones", "descuento", "descuentos", "oferta", "ofertas", "vigentes", "ver", "tienen"}
        browse = mode in {"event_search", "promotion_search"} and not topic
        explicit_venues = matching_venues(db, query) if mode in {'product_search', 'promotion_search'} else []
        scoped_venues = {r['id'] for r in explicit_venues} or None
        if records_override is None and mode in {'navigation', 'venue_info'}:
            named = matching_venues(db, message)
            if named:
                records_override = named[:1]
        records = records_override if records_override is not None else search(db, " ".join(topic) if mode in {"event_search", "promotion_search"} else query, kinds=kinds,
            event_day=event_day, browse=browse, maximum_price=preferences.get('budget_bs'),
            venue_ids=scoped_venues, limit=5)
        ordinal = 1 if tokens(message) & {"segundo", "segunda"} else 0
        if follow_up and previous_ids and mode not in {"event_search", "promotion_search"}:
            # Re-run availability checks: a deleted or expired selection is never resurrected.
            available = search(db, query, limit=1000, kinds=kinds, browse=True)
            chosen = previous_ids[min(ordinal, len(previous_ids) - 1)]
            records = [r for r in available if r['id'] == chosen]
            if not records and mode == 'navigation':
                selected = next((r for r in search(db, '', limit=10000, browse=True) if r['id'] == chosen), None)
                if selected and selected['attributes'].get('venue_id'):
                    records = [r for r in available if r['id'] == selected['attributes']['venue_id']]
        if not records and mode == "product_search":
            records = search(db, query, kinds={"venue"})
            if not records and previous_ids and tokens(message) & {'cuesta', 'precio', 'stock'}:
                records = [r for r in search(db, '', kinds={'venue', 'product'}, limit=1000, browse=True)
                           if r['id'] == previous_ids[0]]
        # Cover independently requested destinations rather than one generic ranking.
        clauses = re.split(r"\s+y\s+|[;,]", message)
        if mode in {"discovery", "product_search"} and len(clauses) > 1 and not follow_up:
            records = []
            unanswered = []
            for clause in clauses[:3]:
                candidates = search(db, clause, limit=1, kinds={'product'}, maximum_price=preferences.get('budget_bs'), venue_ids={r['id'] for r in matching_venues(db, clause)} or None) if mode == "product_search" else []
                candidates = candidates or search(db, clause, limit=1, kinds={"venue", "faq", "product"})
                records.extend(r for r in candidates if r['id'] not in {x['id'] for x in records})
                if not candidates:
                    unanswered.append(clause.strip())
        else:
            unanswered = []
        if preferences.get('budget_bs') is not None and mode in {'discovery', 'product_search'}:
            maximum = preferences['budget_bs']
            records = [r for r in records if r['kind'] != 'product' or r['attributes'].get('price_bs') is not None and r['attributes']['price_bs'] <= maximum]
        linked_venues = {r['id']: r for r in search(db, '', kinds={'venue'}, limit=10000, browse=True)}
        for record in records:
            a = record['attributes']
            venue = linked_venues.get(a.get('venue_id')) if record['kind'] in {'product', 'promotion'} else None
            if venue:
                a.setdefault('venue_name', venue['title'])
                a.setdefault('venue_source_url', venue['source_url'])
                for field in ('floor', 'unit', 'area', 'tower', 'reference'):
                    if venue['attributes'].get(field):
                        a.setdefault(field, venue['attributes'][field])
        evidence = records[:3]
        has_demo = any(r['attributes'].get('data_origin') == 'synthetic_demo' for r in evidence)
        answer = None
        result = {"session_id": session_id, "intent": mode,
                  "answer": answer or (navigation_answer(evidence[0] if evidence else None)
                                       if mode == "navigation" else typed_answer(evidence, mode, message) or FALLBACK),
                  "sources": [{**{k: r[k] for k in ("id", "kind", "title", "attributes", "source_url", "updated_at")}, "expires_at": r.get("expires_at")}
                              for r in evidence],
                  "suggestions": [r["title"] for r in evidence],
                  "grounded": True,
                  "answer_mode": "experimental" if answer else STRICT_RESPONSE_MODE,
                  "guide": {"destination_id": evidence[0]["id"], "floor": evidence[0]["attributes"].get("floor"),
                            "unit": evidence[0]["attributes"].get("unit")}
                  if mode == "navigation" and evidence else None}
        if unanswered:
            result['answer'] += ' No tengo información confirmada para: ' + '; '.join(unanswered) + '.'
        result['contains_demo_data'] = has_demo
        if mode == 'promotion_search':
            result['suggestions'] = [f"Promoción de {r['attributes'].get('venue_name', r['title'])}" for r in evidence]
        if mode in {'discovery', 'product_search'} and not follow_up and not preference_reply:
            preferences['topic'] = message
        if mode in {'discovery', 'product_search'} and preferences.get('budget_bs') is not None:
            result['answer'] += f" Presupuesto de esta conversación: Bs {preferences['budget_bs']:g}; los negocios sin catálogo no tienen precio confirmado."
    if shop_result is not None and any(r['kind'] == 'product' for r in result.get('sources', [])):
        venue_map = {r['id']: r for r in search(db, '', kinds={'venue'}, browse=True, limit=10000)}
        for record in result['sources']:
            venue = venue_map.get(record['attributes'].get('venue_id'))
            if venue:
                for field in ('floor', 'unit', 'area', 'tower'):
                    if venue['attributes'].get(field):
                        record['attributes'].setdefault(field, venue['attributes'][field])
    result['preferences'] = {key: preferences[key] for key in ('budget_bs', 'recipient') if key in preferences}
    if result.get('dialogue_stage') in {'shops', 'catalog', 'clarify', 'welcome'}:
        preferences['dialogue_stage'] = result['dialogue_stage']
    result['contains_demo_data'] = result.get('contains_demo_data', False) or any(
        r['attributes'].get('data_origin') == 'synthetic_demo' or r['attributes'].get('hours_origin') == 'synthetic_demo'
        for r in result.get('sources', []))
    stamp = datetime.now(timezone.utc).isoformat()
    db.execute('INSERT INTO session_preferences VALUES (?, ?, ?) ON CONFLICT(session_id) DO UPDATE SET preferences=excluded.preferences, updated_at=excluded.updated_at',
               (session_id, json.dumps(preferences, ensure_ascii=False), stamp))
    if result.get('sources') and mode not in {'hours', 'weather'}:
        db.execute("INSERT INTO session_context VALUES (?, ?, ?) ON CONFLICT(session_id) DO UPDATE SET record_ids=excluded.record_ids, updated_at=excluded.updated_at",
                   (session_id, json.dumps([r['id'] for r in result['sources']]), stamp))
    db.executemany("INSERT INTO turns(session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                   [(session_id, "user", message, stamp), (session_id, "assistant", result["answer"], stamp)])
    db.execute("DELETE FROM turns WHERE created_at < ?", ((datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),))
    db.execute("DELETE FROM session_context WHERE updated_at < ?", ((datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),))
    db.commit()
    return result
