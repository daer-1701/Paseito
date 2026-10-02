"""Small cached weather adapter for Cochabamba, with a source per response."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone


WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
PARAMS = {
    "latitude": "-17.3935", "longitude": "-66.1570", "current": "temperature_2m,apparent_temperature,precipitation,weather_code",
    "timezone": "America/La_Paz",
}
CACHE_SECONDS = 600
_cached: tuple[float, dict] | None = None

WMO = {
    0: "cielo despejado", 1: "mayormente despejado", 2: "parcialmente nublado", 3: "nublado",
    45: "niebla", 48: "niebla con escarcha", 51: "llovizna ligera", 53: "llovizna", 55: "llovizna intensa",
    61: "lluvia ligera", 63: "lluvia", 65: "lluvia intensa", 80: "chubascos ligeros", 81: "chubascos", 82: "chubascos intensos",
    95: "tormenta",
}


def current_weather() -> dict:
    global _cached
    if _cached and time.monotonic() - _cached[0] < CACHE_SECONDS:
        return _cached[1]
    url = WEATHER_URL + "?" + urllib.parse.urlencode(PARAMS)
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.load(response)
        current = payload["current"]
        temperature = float(current["temperature_2m"])
        apparent = float(current["apparent_temperature"])
        code = int(current["weather_code"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("weather data is unavailable") from exc
    observed = str(current.get("time") or datetime.now(timezone.utc).isoformat())
    result = {
        "answer": f"En Cochabamba hay {WMO.get(code, 'condiciones variables')}, {temperature:.0f} °C y sensación de {apparent:.0f} °C.",
        "sources": [{
            "id": "weather:cochabamba", "kind": "faq", "title": "Clima actual de Cochabamba",
            "attributes": {"temperature_c": temperature, "apparent_temperature_c": apparent,
                           "condition": WMO.get(code, "condiciones variables"), "observed_at": observed,
                           "cache_seconds": CACHE_SECONDS},
            "source_url": url, "updated_at": observed,
        }],
    }
    _cached = (time.monotonic(), result)
    return result
