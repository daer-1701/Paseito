"""Device-neutral gaze events for optional eye-tracker integration."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone

import os


MIN_DWELL_MS = 900
COOLDOWN_SECONDS = 12
_last_trigger: dict[tuple[str, str], float] = {}
_lock = threading.Lock()


def gaze(db, session_id: str, target_id: str, dwell_ms: int, welcome: bool = False, busy: bool = True, manual: bool = False) -> dict:
    if not isinstance(session_id, str) or not 0 < len(session_id) <= 100:
        raise ValueError("session_id is required")
    if not isinstance(target_id, str) or not 0 < len(target_id) <= 100:
        raise ValueError("target_id is required")
    if not isinstance(dwell_ms, int) or not 0 <= dwell_ms <= 15000:
        raise ValueError("dwell_ms must be between 0 and 15000")
    if isinstance(dwell_ms, bool):
        raise ValueError('dwell_ms must be an integer')
    if target_id != 'gaze_at_kiosk':
        return {'triggered': False, 'reason': 'unsupported_target'}
    if not manual and os.getenv('JARVIS_STIMULUS_ENABLED') != '1':
        return {'triggered': False, 'reason': 'device_disabled'}
    if manual and os.getenv('JARVIS_DEMO_CATALOG') != '1':
        return {'triggered': False, 'reason': 'demo_disabled'}
    if not welcome or busy:
        return {'triggered': False, 'reason': 'not_idle_welcome'}
    if db.execute('SELECT 1 FROM turns WHERE session_id=? LIMIT 1',(session_id,)).fetchone():
        return {'triggered': False, 'reason': 'conversation_active'}
    if dwell_ms < MIN_DWELL_MS:
        return {"triggered": False, "reason": "dwell_too_short"}
    key = (session_id, target_id)
    with _lock:
        now = time.monotonic()
        db.execute('CREATE TABLE IF NOT EXISTS stimulus_welcome (session_id TEXT PRIMARY KEY, created_at TEXT NOT NULL)')
        db.execute('DELETE FROM stimulus_welcome WHERE created_at < ?', ((datetime.now(timezone.utc)-timedelta(days=1)).isoformat(),))
        if db.execute('SELECT 1 FROM stimulus_welcome WHERE session_id=?',(session_id,)).fetchone():
            return {'triggered': False, 'reason': 'already_greeted'}
        if now - _last_trigger.get(key, -COOLDOWN_SECONDS) < COOLDOWN_SECONDS:
            return {'triggered': False, 'reason': 'cooldown'}
        _last_trigger[key] = now
        if len(_last_trigger) > 10000:
            _last_trigger.clear()
        stamp = datetime.now(timezone.utc).isoformat()
        db.execute('INSERT INTO stimulus_welcome VALUES (?,?)',(session_id,stamp))
        db.commit()
    result = {'session_id':session_id, 'intent':'stimulus', 'answer':'¡Hola! Soy Paseito, tu asistente del Paseo Aranjuez. ¿Qué te gustaría encontrar?',
              'sources':[], 'suggestions':[], 'grounded':True, 'answer_mode':'strict', 'dialogue_stage':'welcome'}
    return {"triggered": True, "chat": result}
