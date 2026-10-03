"""Shared channel analytics, redacted text and 30 day retention."""
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from .context import BOLIVIA
from .store import tokens


def redact(text):
    text = re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[correo]', text)
    return re.sub(r'(?<!\w)\+?\d[\d ()-]{6,}\d(?!\w)', '[dato]', text)[:2000]


def schema(db):
    db.execute('''CREATE TABLE IF NOT EXISTS consultas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
        canal TEXT NOT NULL, texto TEXT NOT NULL, herramientas TEXT NOT NULL,
        sin_resultados INTEGER NOT NULL, duracion_ms INTEGER NOT NULL,
        proveedor TEXT NOT NULL, error TEXT, creado TEXT NOT NULL)''')
    db.execute('CREATE INDEX IF NOT EXISTS idx_consultas_creado ON consultas(creado)')


def record(db, message, result, channel, duration, uses, error=None):
    schema(db)
    missing = not result.get('sources') and not result.get('tarjetas') and result.get('dialogue_stage') not in {'welcome', 'clarify'} and result.get('intent') not in {'loyalty', 'order', 'weather', 'stimulus'}
    db.execute('INSERT INTO consultas(session_id,canal,texto,herramientas,sin_resultados,duracion_ms,proveedor,error,creado) VALUES(?,?,?,?,?,?,?,?,?)',
               (result['session_id'], channel, redact(message), json.dumps(uses, ensure_ascii=False), int(missing), duration,
                result['answer_mode'], error, datetime.now(timezone.utc).isoformat()))
    db.execute('DELETE FROM consultas WHERE creado < ?', ((datetime.now(timezone.utc)-timedelta(days=30)).isoformat(),))
    db.commit()


def summary(db, top=10):
    schema(db)
    rows = [dict(r) for r in db.execute('SELECT * FROM consultas ORDER BY id DESC')]
    terms, unmet, tools, hours, channels, providers, errors = (Counter() for _ in range(7))
    today = datetime.now(BOLIVIA).date()
    for r in rows:
        channels[r['canal']] += 1
        providers[r['proveedor']] += 1
        if r['error']: errors[r['error']] += 1
        hours[datetime.fromisoformat(r['creado']).astimezone(BOLIVIA).strftime('%H:00')] += 1
        for use in json.loads(r['herramientas']): tools[use['nombre']] += 1
        for word in tokens(r['texto']) - {'hola','buenas','tienes','tienen','busco','muestrame','dame','quiero'}:
            terms[word] += 1
            if r['sin_resultados']: unmet[word] += 1
    n = len(rows)
    return {'total_consultas':n,'consultas_hoy':sum(datetime.fromisoformat(r['creado']).astimezone(BOLIVIA).date()==today for r in rows),
            'sesiones':len({r['session_id'] for r in rows}), 'tasa_sin_resultados':round(sum(r['sin_resultados'] for r in rows)/n,3) if n else 0,
            'duracion_promedio_ms':round(sum(r['duracion_ms'] for r in rows)/n) if n else 0,
            'mas_buscado':[{'termino':t,'veces':v} for t,v in terms.most_common(top)],
            'demanda_no_cubierta':[{'termino':t,'veces':v} for t,v in unmet.most_common(top)],
            'uso_herramientas':dict(tools),'consultas_por_hora':dict(sorted(hours.items())),
            'canales':dict(channels),'proveedores':dict(providers),'errores':dict(errors),
            'ultimas_sin_resultado':[{'texto':r['texto'],'fecha':r['creado']} for r in rows if r['sin_resultados']][:top]}
