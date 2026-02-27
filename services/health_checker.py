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
    get_metric_with_timeout,
    get_network_best_block,
    get_peers_count,
    measure_rpc_response_time,
)


async def collect_all_metrics(node: Node) -> HealthMetrics:
    timestamp = datetime.now(timezone.utc)

    async def block_height() -> int | None:
        return await get_metric_with_timeout(lambda: get_block_height(node))

    async def network_best_block() -> int | None:
        return await get_metric_with_timeout(get_network_best_block)

    async def peers_count() -> int | None:
        return await get_metric_with_timeout(lambda: get_peers_count(node))

    async def finality_lag() -> int | None:
        return await get_metric_with_timeout(lambda: get_finality_lag(node))

    async def rpc_response_time() -> float | None:
        value = await get_metric_with_timeout(lambda: measure_rpc_response_time(node))
        if value is None or value < 0:
            return None
        return value

    async def time_since_last_block() -> int | None:
        last_ts = await get_metric_with_timeout(lambda: get_last_block_timestamp(node))
        if last_ts is None:
            return None
        return await calculate_time_since_last_block(last_ts)

    (
        block_height_value,
        network_best_block_value,
        peers_count_value,
        finality_lag_value,
        rpc_response_time_value,
        time_since_last_value,
    ) = await asyncio.gather(
        block_height(),
        network_best_block(),
        peers_count(),
        finality_lag(),
        rpc_response_time(),
        time_since_last_block(),
    )

    metrics = HealthMetrics(
        node_name=node.name,
        timestamp=timestamp,
        block_height=block_height_value,
        current_block_height=network_best_block_value,
        peers_count=peers_count_value,
        finality_lag=finality_lag_value,
        time_since_last_block=time_since_last_value,
        rpc_response_time=rpc_response_time_value,
    )

    metrics.status = await evaluate_overall_health(metrics)
    return metrics


async def evaluate_overall_health(metrics: HealthMetrics) -> str:
    statuses: list[str] = []

    if metrics.peers_count is None:
        statuses.append("unknown")
    else:
        statuses.append(await evaluate_peers_health(metrics.peers_count))

    if metrics.finality_lag is None:
        statuses.append("unknown")
    else:
        statuses.append(await evaluate_finality_health(metrics.finality_lag))

    if metrics.rpc_response_time is None:
        statuses.append("unknown")
    else:
        statuses.append("healthy")

    if metrics.time_since_last_block is None:
        statuses.append("unknown")
    else:
        statuses.append("healthy")

    if metrics.block_height is None or metrics.current_block_height is None:
        statuses.append("unknown")
    elif metrics.block_height < metrics.current_block_height:
        statuses.append("warning")
    else:
        statuses.append("healthy")

    yellows = sum(1 for s in statuses if s in {"warning", "unknown"})
    reds = sum(1 for s in statuses if s == "critical")

    if reds >= 1 or yellows >= 3:
        return "critical"
    if yellows >= 1:
        return "warning"
    return "healthy"