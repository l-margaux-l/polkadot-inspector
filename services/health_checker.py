from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from models.metrics import HealthMetrics
from models.node import Node
from services.metrics_collector import (
    calculate_time_since_last_block,
    evaluate_finality_health,
    evaluate_peers_health,
    get_block_height,
    get_finality_lag,
    get_last_block_timestamp,
    get_network_best_block,
    get_peers_count,
    measure_rpc_response_time,
)


async def collect_all_metrics(node: Node) -> HealthMetrics:
    timestamp = datetime.now(timezone.utc)

    async def time_since_last_block() -> int:
        last_ts = await get_last_block_timestamp(node)
        return await calculate_time_since_last_block(last_ts)

    (
        block_height,
        network_best_block,
        peers_count,
        finality_lag,
        rpc_response_time,
        time_since_last,
    ) = await asyncio.gather(
        get_block_height(node),
        get_network_best_block(),
        get_peers_count(node),
        get_finality_lag(node),
        measure_rpc_response_time(node),
        time_since_last_block(),
    )

    metrics = HealthMetrics(
        node_name=node.name,
        timestamp=timestamp,
        block_height=block_height,
        current_block_height=network_best_block,
        peers_count=peers_count,
        finality_lag=finality_lag,
        time_since_last_block=time_since_last,
        rpc_response_time=rpc_response_time,
    )

    metrics.status = await evaluate_overall_health(metrics)
    return metrics


async def evaluate_overall_health(metrics: HealthMetrics) -> str:
    statuses: list[str] = []

    if metrics.peers_count is None:
        statuses.append("critical")
    else:
        statuses.append(await evaluate_peers_health(metrics.peers_count))

    if metrics.finality_lag is None:
        statuses.append("critical")
    else:
        statuses.append(await evaluate_finality_health(metrics.finality_lag))

    if metrics.rpc_response_time is None or metrics.rpc_response_time < 0:
        statuses.append("critical")
    else:
        statuses.append("healthy")

    if metrics.time_since_last_block is None:
        statuses.append("critical")
    else:
        statuses.append("healthy")

    if metrics.block_height is None or metrics.current_block_height is None:
        statuses.append("critical")
    elif metrics.block_height < metrics.current_block_height:
        statuses.append("warning")
    else:
        statuses.append("healthy")

    yellows = sum(1 for s in statuses if s == "warning")
    reds = sum(1 for s in statuses if s == "critical")

    if reds >= 1 or yellows >= 3:
        return "critical"
    if yellows >= 1:
        return "warning"
    return "healthy"