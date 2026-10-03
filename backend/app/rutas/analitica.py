import json
from collections import Counter
from datetime import datetime, time

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..config import ZONA_HORARIA
from ..db import get_session
from ..herramientas import ahora, normalizar
from ..models import Consulta
from .admin import verificar_admin

router = APIRouter(prefix="/analitica", tags=["analítica"], dependencies=[Depends(verificar_admin)])


@router.get("/resumen")
def resumen(top: int = 10, db: Session = Depends(get_session)):
    consultas = db.exec(select(Consulta).order_by(Consulta.creado.desc())).all()
    inicio_hoy = datetime.combine(ahora().date(), time.min, tzinfo=ZONA_HORARIA)

    palabras: Counter = Counter()
    palabras_sin_resultado: Counter = Counter()
    herramientas: Counter = Counter()
    por_hora: Counter = Counter()

    for c in consultas:
        por_hora[c.creado.hour] += 1
        for uso in json.loads(c.herramientas or "[]"):
            herramientas[uso["nombre"]] += 1
            args = uso.get("argumentos", {})
            terminos = args.get("palabras_clave") or [args.get("nombre") or args.get("tema") or ""]
            for termino in terminos:
                termino = normalizar(str(termino)).strip()
                if not termino:
                    continue
                palabras[termino] += 1
                if uso.get("resultados", 0) == 0:
                    palabras_sin_resultado[termino] += 1

    total = len(consultas)
    return {
        "total_consultas": total,
        "consultas_hoy": sum(1 for c in consultas if c.creado >= inicio_hoy),
        "sesiones": len({c.session_id for c in consultas}),
        "tasa_sin_resultados": round(sum(c.sin_resultados for c in consultas) / total, 3) if total else 0,
        "duracion_promedio_ms": int(sum(c.duracion_ms for c in consultas) / total) if total else 0,
        "mas_buscado": [{"termino": t, "veces": n} for t, n in palabras.most_common(top)],
        "demanda_no_cubierta": [{"termino": t, "veces": n} for t, n in palabras_sin_resultado.most_common(top)],
        "uso_herramientas": dict(herramientas.most_common()),
        "consultas_por_hora": {f"{h:02d}:00": por_hora[h] for h in sorted(por_hora)},
        "ultimas_sin_resultado": [
            {"texto": c.texto, "fecha": c.creado.isoformat(timespec="minutes")}
            for c in consultas if c.sin_resultados
        ][:top],
    }


@router.get("/consultas")
def listar_consultas(limite: int = 50, db: Session = Depends(get_session)):
    consultas = db.exec(select(Consulta).order_by(Consulta.creado.desc()).limit(limite)).all()
    return [
        {**c.model_dump(exclude={"herramientas"}), "herramientas": json.loads(c.herramientas or "[]")}
        for c in consultas
    ]
