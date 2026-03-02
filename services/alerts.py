from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from models.metrics import HealthMetrics


ALERT_LEVEL_INFO = "info"
ALERT_LEVEL_WARNING = "warning"
ALERT_LEVEL_CRITICAL = "critical"


@dataclass(slots=True)
class Alert:
    level: str
    message: str
    timestamp: datetime


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def check_alerts(metrics: HealthMetrics) -> List[Alert]:
    alerts: List[Alert] = []
    now = _now_utc()

    if metrics.block_height is not None and metrics.current_block_height is not None:
        lag = metrics.current_block_height - metrics.block_height
        if lag > 50:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_CRITICAL,
                    message=f"Block height lag is too high: {lag}",
                    timestamp=now,
                )
            )
        elif lag > 20:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_WARNING,
                    message=f"Block height lag is elevated: {lag}",
                    timestamp=now,
                )
            )

    if metrics.peers_count is not None:
        if metrics.peers_count <= 5:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_CRITICAL,
                    message=f"Low peers count: {metrics.peers_count}",
                    timestamp=now,
                )
            )
        elif metrics.peers_count <= 20:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_WARNING,
                    message=f"Moderate peers count: {metrics.peers_count}",
                    timestamp=now,
                )
            )

    if metrics.finality_lag is not None:
        if metrics.finality_lag == 0 or metrics.finality_lag > 30:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_CRITICAL,
                    message=f"Finality lag is critical: {metrics.finality_lag}",
                    timestamp=now,
                )
            )
        elif metrics.finality_lag >= 10:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_WARNING,
                    message=f"Finality lag is elevated: {metrics.finality_lag}",
                    timestamp=now,
                )
            )

    if metrics.rpc_response_time is not None:
        if metrics.rpc_response_time > 2000:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_CRITICAL,
                    message=f"RPC response time is too high: {metrics.rpc_response_time:.0f} ms",
                    timestamp=now,
                )
            )
        elif metrics.rpc_response_time > 1000:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_WARNING,
                    message=f"RPC response time is elevated: {metrics.rpc_response_time:.0f} ms",
                    timestamp=now,
                )
            )

    if metrics.time_since_last_block is not None:
        if metrics.time_since_last_block > 120:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_CRITICAL,
                    message=f"Time since last block is too high: {metrics.time_since_last_block} s",
                    timestamp=now,
                )
            )
        elif metrics.time_since_last_block > 60:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_WARNING,
                    message=f"Time since last block is elevated: {metrics.time_since_last_block} s",
                    timestamp=now,
                )
            )

    if metrics.status == "critical":
        alerts.append(
            Alert(
                level=ALERT_LEVEL_CRITICAL,
                message="Overall node health is critical",
                timestamp=now,
            )
        )
    elif metrics.status == "warning":
        alerts.append(
            Alert(
                level=ALERT_LEVEL_WARNING,
                message="Overall node health is degraded",
                timestamp=now,
            )
        )

    return alerts