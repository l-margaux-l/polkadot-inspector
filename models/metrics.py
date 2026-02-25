from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

HealthStatus = Literal["healthy", "warning", "critical"]


@dataclass(slots=True)
class HealthMetrics:
    node_name: str
    timestamp: datetime

    block_height: int | None = None
    current_block_height: int | None = None
    peers_count: int | None = None
    finality_lag: int | None = None
    time_since_last_block: int | None = None
    rpc_response_time: float | None = None

    status: HealthStatus = "healthy"