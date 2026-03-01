from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from models.metrics import HealthMetrics


CSV_FIELDS = [
    "timestamp",
    "node_name",
    "block_height",
    "current_block_height",
    "peers_count",
    "finality_lag",
    "time_since_last_block",
    "rpc_response_time",
    "status",
]


def _metrics_to_row(m: HealthMetrics) -> dict[str, object]:
    return {
        "timestamp": m.timestamp.isoformat(),
        "node_name": m.node_name,
        "block_height": m.block_height,
        "current_block_height": m.current_block_height,
        "peers_count": m.peers_count,
        "finality_lag": m.finality_lag,
        "time_since_last_block": m.time_since_last_block,
        "rpc_response_time": m.rpc_response_time,
        "status": m.status,
    }


def export_metrics_to_csv(metrics_list: List[HealthMetrics], filename: str) -> None:
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for m in metrics_list:
            writer.writerow(_metrics_to_row(m))


def _row_to_metrics(row: dict[str, str]) -> HealthMetrics:
    from datetime import datetime

    timestamp = datetime.fromisoformat(row["timestamp"])
    def _to_int(value: str) -> int | None:
        return int(value) if value not in ("", "None") else None

    def _to_float(value: str) -> float | None:
        return float(value) if value not in ("", "None") else None

    return HealthMetrics(
        node_name=row["node_name"],
        timestamp=timestamp,
        block_height=_to_int(row.get("block_height", "")),
        current_block_height=_to_int(row.get("current_block_height", "")),
        peers_count=_to_int(row.get("peers_count", "")),
        finality_lag=_to_int(row.get("finality_lag", "")),
        time_since_last_block=_to_int(row.get("time_since_last_block", "")),
        rpc_response_time=_to_float(row.get("rpc_response_time", "")),
        status=row.get("status", "unknown"),
    )


def load_metrics_from_csv(filename: str) -> List[HealthMetrics]:
    path = Path(filename)
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            _row_to_metrics(row)
            for row in reader
        ]