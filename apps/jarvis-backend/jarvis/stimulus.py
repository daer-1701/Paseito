"""Device-neutral gaze events for optional eye-tracker integration."""

from __future__ import annotations

import threading
import time
import json
from datetime import datetime, timezone

from .agent import chat
from .store import parse_timestamp


MIN_DWELL_MS = 900
COOLDOWN_SECONDS = 12
_last_trigger: dict[tuple[str, str], float] = {}
_lock = threading.Lock()


def gaze(db, session_id: str, target_id: str, dwell_ms: int) -> dict:
    if not isinstance(session_id, str) or not 0 < len(session_id) <= 100:
        raise ValueError("session_id is required")
    if not isinstance(target_id, str) or not 0 < len(target_id) <= 100:
        raise ValueError("target_id is required")
    if not isinstance(dwell_ms, int) or not 0 <= dwell_ms <= 15000:
        raise ValueError("dwell_ms must be between 0 and 15000")
    if dwell_ms < MIN_DWELL_MS:
        return {"triggered": False, "reason": "dwell_too_short"}
    row = db.execute("SELECT * FROM records WHERE id=?", (target_id,)).fetchone()
    if not row or (row["expires_at"] and parse_timestamp(row["expires_at"]) <= datetime.now(timezone.utc)):
        return {"triggered": False, "reason": "target_unavailable"}
    key = (session_id, target_id)
    with _lock:
        now = time.monotonic()
        if now - _last_trigger.get(key, -COOLDOWN_SECONDS) < COOLDOWN_SECONDS:
            return {"triggered": False, "reason": "cooldown"}
        _last_trigger[key] = now
        if len(_last_trigger) > 10000:
            _last_trigger.clear()
    record = dict(row)
    record["attributes"] = json.loads(record["attributes"])
    result = chat(db, f"Cuéntame sobre {row['title']}", session_id,
                  records_override=[record])
    return {"triggered": True, "chat": result}
