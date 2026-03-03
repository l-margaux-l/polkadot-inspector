from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from config import ALERT_THRESHOLDS
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

    block_warning = ALERT_THRESHOLDS["block_lag_warning"]
    block_critical = ALERT_THRESHOLDS["block_lag_critical"]
    peers_warning = ALERT_THRESHOLDS["peers_warning"]
    peers_critical = ALERT_THRESHOLDS["peers_critical"]
    ts_warning = ALERT_THRESHOLDS["time_since_block_warning"]
    ts_critical = ALERT_THRESHOLDS["time_since_block_critical"]
    rpc_warning = ALERT_THRESHOLDS["rpc_response_warning"]
    rpc_critical = ALERT_THRESHOLDS["rpc_response_critical"]
    finality_warning = ALERT_THRESHOLDS["finality_lag_warning"]
    finality_critical = ALERT_THRESHOLDS["finality_lag_critical"]

    if metrics.block_height is not None and metrics.current_block_height is not None:
        lag = metrics.current_block_height - metrics.block_height
        if lag >= block_critical:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_CRITICAL,
                    message=f"Block height lag is too high: {lag}",
                    timestamp=now,
                )
            )
        elif lag >= block_warning:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_WARNING,
                    message=f"Block height lag is elevated: {lag}",
                    timestamp=now,
                )
            )

    if metrics.peers_count is not None:
        if metrics.peers_count <= peers_critical:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_CRITICAL,
                    message=f"Low peers count: {metrics.peers_count}",
                    timestamp=now,
                )
            )
        elif metrics.peers_count <= peers_warning:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_WARNING,
                    message=f"Moderate peers count: {metrics.peers_count}",
                    timestamp=now,
                )
            )

    if metrics.finality_lag is not None:
        if metrics.finality_lag == 0 or metrics.finality_lag >= finality_critical:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_CRITICAL,
                    message=f"Finality lag is critical: {metrics.finality_lag}",
                    timestamp=now,
                )
            )
        elif metrics.finality_lag >= finality_warning:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_WARNING,
                    message=f"Finality lag is elevated: {metrics.finality_lag}",
                    timestamp=now,
                )
            )

    if metrics.rpc_response_time is not None:
        if metrics.rpc_response_time >= rpc_critical:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_CRITICAL,
                    message=(
                        "RPC response time is too high: "
                        f"{metrics.rpc_response_time:.0f} ms"
                    ),
                    timestamp=now,
                )
            )
        elif metrics.rpc_response_time >= rpc_warning:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_WARNING,
                    message=(
                        "RPC response time is elevated: "
                        f"{metrics.rpc_response_time:.0f} ms"
                    ),
                    timestamp=now,
                )
            )

    if metrics.time_since_last_block is not None:
        if metrics.time_since_last_block >= ts_critical:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_CRITICAL,
                    message=(
                        "Time since last block is too high: "
                        f"{metrics.time_since_last_block} s"
                    ),
                    timestamp=now,
                )
            )
        elif metrics.time_since_last_block >= ts_warning:
            alerts.append(
                Alert(
                    level=ALERT_LEVEL_WARNING,
                    message=(
                        "Time since last block is elevated: "
                        f"{metrics.time_since_last_block} s"
                    ),
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