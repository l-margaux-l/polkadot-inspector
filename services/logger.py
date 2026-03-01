from __future__ import annotations

import json
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from config import LOGS_DIR
from models.metrics import HealthMetrics


LOG_FILE_NAME = "inspector.log"


class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "timestamp": self.formatTime(record),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            payload.update(record.extra_data)
        return json.dumps(payload, ensure_ascii=False)


def setup_logger() -> logging.Logger:
    logs_path = Path(LOGS_DIR)
    logs_path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("inspector")
    logger.setLevel(logging.INFO)

    if any(isinstance(h, TimedRotatingFileHandler) for h in logger.handlers):
        return logger

    log_file = logs_path / LOG_FILE_NAME
    handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",
        backupCount=7,
        encoding="utf-8",
        utc=True,
    )
    formatter = JsonLineFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.propagate = False
    return logger


def _metrics_to_dict(metrics: HealthMetrics) -> dict[str, object]:
    return {
        "node_name": metrics.node_name,
        "timestamp": metrics.timestamp.isoformat(),
        "block_height": metrics.block_height,
        "current_block_height": metrics.current_block_height,
        "peers_count": metrics.peers_count,
        "finality_lag": metrics.finality_lag,
        "time_since_last_block": metrics.time_since_last_block,
        "rpc_response_time": metrics.rpc_response_time,
        "status": metrics.status,
    }


def log_metrics(metrics: HealthMetrics) -> None:
    logger = setup_logger()
    logger.info("node health metrics", extra={"extra_data": _metrics_to_dict(metrics)})