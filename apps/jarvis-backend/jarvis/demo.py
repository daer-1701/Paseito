"""Opt-in demo fields without replacing the sourced tenant records."""
import json
import os
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def schedules():
    path = Path(__file__).resolve().parents[1] / 'data' / 'demo-schedules.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def with_demo_hours(record_id, attrs):
    if os.getenv('JARVIS_DEMO_CATALOG') != '1' or attrs.get('hours'):
        return attrs
    schedule = schedules().get(record_id)
    if not schedule:
        return attrs
    return {**attrs, 'hours': schedule, 'hours_origin': 'synthetic_demo', 'demo_fields': ['hours']}
