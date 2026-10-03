"""Sourced, time-aware context for the Paseo's public areas."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


PASEO_URL = "https://paseoaranjuez.com/"
SCHEDULE_OBSERVED_AT = "2026-10-03T00:00:00-04:00"
BOLIVIA = ZoneInfo("America/La_Paz")

# These are area schedules published on the official Paseo page.  They do not
# prove that a particular tenant is open, so answers deliberately retain scope.
AREAS = (
    {
        "id": "hours:commerce",
        "title": "Tiendas y comercios del Paseo",
        "attributes": {"scope": "horario general del área comercial", "mon_sat": ["10:00", "22:00"],
                       "sun_holiday": ["12:00", "22:00"]},
    },
    {
        "id": "hours:food-court",
        "title": "Mercado gastronómico",
        "attributes": {"scope": "horario general del mercado gastronómico", "mon_sat": ["11:00", "23:00"],
                       "sun_holiday": ["12:00", "22:00"]},
    },
    {
        "id": "hours:el-cuarto",
        "title": "El Cuarto",
        "attributes": {"scope": "horario publicado para El Cuarto", "mon_thu": ["12:00", "23:00"],
                       "fri_sat": ["12:00", "01:00"], "sun_holiday": ["12:00", "22:00"]},
    },
)


def _minutes(value: str) -> int:
    hour, minute = (int(piece) for piece in value.split(":"))
    return hour * 60 + minute


def _range(area: dict, now: datetime) -> tuple[str, str]:
    day = now.weekday()
    attrs = area["attributes"]
    if day == 6:
        return tuple(attrs["sun_holiday"])
    if area["id"] == "hours:el-cuarto":
        return tuple(attrs["fri_sat"] if day in {4, 5} else attrs["mon_thu"])
    return tuple(attrs["mon_sat"])


def _is_open(area: dict, now: datetime) -> bool:
    current = now.hour * 60 + now.minute
    opens, closes = _range(area, now)
    start, end = _minutes(opens), _minutes(closes)
    opened_today = current >= start and (end <= start or current < end)
    previous_opens, previous_closes = _range(area, now - timedelta(days=1))
    previous_start, previous_end = _minutes(previous_opens), _minutes(previous_closes)
    return opened_today or (previous_end <= previous_start and current < previous_end)


def opening_status(now: datetime | None = None) -> dict:
    now = (now or datetime.now(BOLIVIA)).astimezone(BOLIVIA)
    entries = []
    for area in AREAS:
        opens, closes = _range(area, now)
        entries.append({
            "id": area["id"], "kind": "faq", "title": area["title"],
            "attributes": {**area["attributes"], "opens": opens, "closes": closes,
                           "open_now": _is_open(area, now),
                           "review_status": "sourced", "observed_at": SCHEDULE_OBSERVED_AT},
            "source_url": PASEO_URL,
            "updated_at": SCHEDULE_OBSERVED_AT,
        })
    labels = []
    for entry in entries:
        attrs = entry["attributes"]
        state = "está abierto" if attrs["open_now"] else "está cerrado"
        labels.append(f"{entry['title']} {state} ({attrs['opens']}–{attrs['closes']})")
    holiday_note = " El horario de domingo también aplica a feriados." if now.weekday() == 6 else ""
    answer = f"Ahora son las {now:%H:%M} en Cochabamba. " + "; ".join(labels) + "." + holiday_note
    answer += " Los locales individuales pueden tener horarios distintos."
    answer += " Si hoy es feriado, confirma el horario especial; no tengo un calendario de feriados cargado."
    return {"answer": answer, "sources": entries}
