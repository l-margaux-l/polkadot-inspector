from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from models.metrics import HealthMetrics


STATUS_FILE = Path("status.json")


def _now_utc_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def export_status_to_file(metrics_list: List[HealthMetrics]) -> None:
    data = {
        "last_update": _now_utc_z(),
        "nodes": [],
    }

    for m in metrics_list:
        node_entry = {
            "name": m.node_name,
            "status": m.status,
            "block_height": m.block_height,
            "current_block_height": m.current_block_height,
            "peers_count": m.peers_count,
            "finality_lag": m.finality_lag,
            "time_since_last_block": m.time_since_last_block,
            "rpc_response_time": m.rpc_response_time,
            "timestamp": m.timestamp.isoformat(),
        }
        data["nodes"].append(node_entry)

    STATUS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )