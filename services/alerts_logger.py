from __future__ import annotations

import json
from pathlib import Path

from config import LOGS_DIR
from services.alerts import Alert

ALERTS_LOG_FILE = "alerts.jsonl"


def _alerts_log_path() -> Path:
    logs_path = Path(LOGS_DIR)
    logs_path.mkdir(parents=True, exist_ok=True)
    return logs_path / ALERTS_LOG_FILE


def log_alert(alert: Alert) -> None:
    payload = {
        "timestamp": alert.timestamp.isoformat(),
        "level": alert.level,
        "message": alert.message,
    }
    path = _alerts_log_path()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")