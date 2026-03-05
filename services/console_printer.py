from __future__ import annotations

from typing import List

from rich.console import Console
from rich.table import Table

from models.metrics import HealthMetrics
from services.alerts import Alert, ALERT_LEVEL_CRITICAL, ALERT_LEVEL_INFO, ALERT_LEVEL_WARNING

console = Console()


def _status_emoji(status: str) -> str:
    if status == "healthy":
        return "🟢"
    if status == "warning":
        return "🟡"
    if status == "critical":
        return "🔴"
    return "⚪"


def _alert_emoji(level: str) -> str:
    if level == ALERT_LEVEL_CRITICAL:
        return "🔴"
    if level == ALERT_LEVEL_WARNING:
        return "🟡"
    if level == ALERT_LEVEL_INFO:
        return "🟢"
    return "⚪"


def print_metrics_table(metrics_list: List[HealthMetrics]) -> None:
    table = Table(show_header=True, header_style="bold cyan", title="Nodes health")

    table.add_column("Node", style="bold")
    table.add_column("Status")
    table.add_column("Block height", justify="right")
    table.add_column("Finality lag", justify="right")
    table.add_column("Peers", justify="right")
    table.add_column("RPC (ms)", justify="right")
    table.add_column("Since last block (s)", justify="right")

    for m in metrics_list:
        status_icon = _status_emoji(m.status)
        table.add_row(
            m.node_name,
            f"{status_icon} {m.status}",
            str(m.block_height or ""),
            str(m.finality_lag or ""),
            str(m.peers_count or ""),
            f"{m.rpc_response_time:.0f}" if m.rpc_response_time is not None else "",
            str(m.time_since_last_block or ""),
        )

    console.print(table)


def print_alert(alert: Alert) -> None:
    icon = _alert_emoji(alert.level)
    console.print(
        f"{icon} [bold]{alert.level.upper()}[/bold] {alert.message} "
        f"([dim]{alert.timestamp.isoformat()}[/dim])"
    )
