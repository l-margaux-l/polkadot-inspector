from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import List

from services.database import MetricsDB
from models.metrics import HealthMetrics


@dataclass(slots=True)
class NodeStatistics:
    name: str
    uptime: float
    avg_block_lag: float | None
    avg_peers: float | None
    avg_rpc_response: float | None
    incidents: int


def calculate_uptime(node_name: str, hours: int = 24) -> float:
    db = MetricsDB()
    metrics = db.get_metrics_for_node(node_name=node_name, hours=hours)
    if not metrics:
        return 0.0

    total = len(metrics)
    healthy = sum(1 for m in metrics if m.status == "healthy")
    return (healthy / total) * 100.0


def _avg(values: list[float | int | None]) -> float | None:
    numeric_values = [float(v) for v in values if v is not None]
    if not numeric_values:
        return None
    return mean(numeric_values)


def _count_incidents(metrics: List[HealthMetrics]) -> int:
    if not metrics:
        return 0
    incidents = 0
    previous_unhealthy = False
    for m in metrics:
        is_unhealthy = m.status in ("warning", "critical")
        if is_unhealthy and not previous_unhealthy:
            incidents += 1
        previous_unhealthy = is_unhealthy
    return incidents


def _build_node_stats(node_name: str, hours: int) -> NodeStatistics:
    db = MetricsDB()
    metrics = db.get_metrics_for_node(node_name=node_name, hours=hours)
    uptime = 0.0
    if metrics:
        total = len(metrics)
        healthy = sum(1 for m in metrics if m.status == "healthy")
        uptime = (healthy / total) * 100.0

    avg_block_lag = _avg(
        [
            (m.current_block_height - m.block_height)
            for m in metrics
            if m.block_height is not None and m.current_block_height is not None
        ]
    )
    avg_peers = _avg([m.peers_count for m in metrics])
    avg_rpc = _avg([m.rpc_response_time for m in metrics])
    incidents = _count_incidents(metrics)

    return NodeStatistics(
        name=node_name,
        uptime=uptime,
        avg_block_lag=avg_block_lag,
        avg_peers=avg_peers,
        avg_rpc_response=avg_rpc,
        incidents=incidents,
    )


def generate_daily_report(hours: int = 24) -> dict:
    db = MetricsDB()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    conn = db._connect()  
    try:
        cursor = conn.execute(
            """
            SELECT DISTINCT node_name
            FROM metrics
            WHERE timestamp >= ?
            """,
            (since.isoformat(),),
        )
        node_names = [row["node_name"] for row in cursor.fetchall()]
    finally:
        conn.close()

    report_nodes: list[dict] = []
    for name in node_names:
        stats = _build_node_stats(name, hours)
        report_nodes.append(
            {
                "name": stats.name,
                "uptime": round(stats.uptime, 2),
                "avg_block_lag": round(stats.avg_block_lag, 2)
                if stats.avg_block_lag is not None
                else None,
                "avg_peers": round(stats.avg_peers, 2)
                if stats.avg_peers is not None
                else None,
                "avg_rpc_response": round(stats.avg_rpc_response, 2)
                if stats.avg_rpc_response is not None
                else None,
                "incidents": stats.incidents,
            }
        )

    today = datetime.now(timezone.utc).date().isoformat()
    return {
        "date": today,
        "hours": hours,
        "nodes": report_nodes,
    }
