from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from time import perf_counter
from typing import TypeVar

from models.node import Node
from services.rpc_client import connect_to_node, get_chain_head


logger = logging.getLogger(__name__)

T = TypeVar("T")


async def get_metric_with_timeout(metric_func: Callable[[], Awaitable[T]], timeout: float = 5.0) -> T | None:
    try:
        return await asyncio.wait_for(metric_func(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Timeout collecting metric: %s", getattr(metric_func, "__name__", "<unknown>"))
        return None
    except Exception:
        logger.exception("Error collecting metric: %s", getattr(metric_func, "__name__", "<unknown>"))
        return None


async def get_block_height(node: Node) -> int:
    """Fetch current block height from a single node."""
    substrate = await connect_to_node(node.rpc_url)
    head = await asyncio.to_thread(get_chain_head, substrate)
    return int(head["block_height"])


async def get_network_best_block() -> int:
    """Estimate the best known block height using multiple public RPC endpoints."""
    endpoints: list[str] = [
        "wss://rpc.polkadot.io",
        "wss://polkadot.api.onfinality.io/public-ws",
        "https://rpc.polkadot.io",
    ]

    async def fetch_height(rpc_url: str) -> int:
        substrate = await connect_to_node(rpc_url)
        head = await asyncio.to_thread(get_chain_head, substrate)
        return int(head["block_height"])

    results = await asyncio.gather(*(fetch_height(url) for url in endpoints), return_exceptions=True)
    heights: list[int] = [r for r in results if isinstance(r, int)]
    if not heights:
        raise RuntimeError("Unable to determine network best block: all endpoints failed")

    return max(heights)


async def get_peers_count(node: Node) -> int:
    """Fetch connected peers count for a node."""
    substrate = await connect_to_node(node.rpc_url)

    health = await asyncio.to_thread(substrate.rpc_request, "system_health", [])
    health_result = health.get("result")
    if isinstance(health_result, dict) and "peers" in health_result:
        return int(health_result["peers"])

    response = await asyncio.to_thread(substrate.rpc_request, "system_networkState", [])
    result = response.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("Unexpected RPC response for system_networkState")

    connected = result.get("connectedPeers")
    if connected is None:
        connected = result.get("connected_peers")

    if connected is None:
        raise RuntimeError("system_networkState result missing connected peers")
    if not isinstance(connected, dict):
        raise RuntimeError("system_networkState connected peers has unexpected type")

    return len(connected)


async def evaluate_peers_health(peers: int) -> str:
    if peers > 20:
        return "healthy"
    if peers > 5:
        return "warning"
    return "critical"


async def get_last_block_timestamp(node: Node) -> datetime:
    """Fetch the timestamp for the node's current head block (UTC)."""
    substrate = await connect_to_node(node.rpc_url)
    head = await asyncio.to_thread(get_chain_head, substrate)
    block_hash = str(head["block_hash"])
    result = await asyncio.to_thread(
        substrate.query,
        module="Timestamp",
        storage_function="Now",
        params=[],
        block_hash=block_hash,
    )
    timestamp_ms = int(result.value)
    return datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)


async def calculate_time_since_last_block(last_timestamp: datetime) -> int:
    if last_timestamp.tzinfo is None:
        last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    delta = now - last_timestamp.astimezone(timezone.utc)
    seconds = int(delta.total_seconds())
    return seconds if seconds >= 0 else 0


async def measure_rpc_response_time(node: Node) -> float:
    """Measure RPC response time in milliseconds; returns -1.0 on timeout/error."""
    timeout_seconds = 5.0
    start = perf_counter()

    async def do_request() -> None:
        substrate = await connect_to_node(node.rpc_url)
        await asyncio.to_thread(substrate.rpc_request, "system_health", [])

    try:
        await asyncio.wait_for(do_request(), timeout=timeout_seconds)
    except (TimeoutError, Exception):
        return -1.0

    end = perf_counter()
    return (end - start) * 1000.0


async def get_finality_lag(node: Node) -> int:
    """Compute current head height minus finalized head height; returns 0 on failure."""
    try:
        substrate = await connect_to_node(node.rpc_url)
        head = await asyncio.to_thread(get_chain_head, substrate)
        head_height = int(head["block_height"])

        response = await asyncio.to_thread(substrate.rpc_request, "chain_getFinalizedHead", [])
        finalized_hash = response.get("result")
        if not isinstance(finalized_hash, str) or not finalized_hash:
            return 0

        finalized_height = int(substrate.get_block_number(finalized_hash))
        lag = head_height - finalized_height
        return lag if lag >= 0 else 0
    except Exception:
        return 0


async def evaluate_finality_health(lag: int) -> str:
    if lag == 0 or lag > 30:
        return "critical"
    if lag >= 10:
        return "warning"
    return "healthy"