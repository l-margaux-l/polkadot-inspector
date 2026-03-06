from __future__ import annotations

from time import perf_counter
from typing import Dict, List

from config import NODES_CONFIG_PATH
from models.node import Node
from services.metrics_collector import (
    get_block_height,
    get_peers_count,
    measure_rpc_response_time,
)
from services.nodes_config import NodeConfig, load_nodes_config


def _ms(start: float, end: float) -> float:
    return (end - start) * 1000.0


async def benchmark_node(node: Node) -> Dict[str, float]:
    timings: Dict[str, float] = {}

    start = perf_counter()
    await get_block_height(node)
    end = perf_counter()
    timings["block_height"] = _ms(start, end)

    start = perf_counter()
    await get_peers_count(node)
    end = perf_counter()
    timings["peers"] = _ms(start, end)

    start = perf_counter()
    await measure_rpc_response_time(node)
    end = perf_counter()
    timings["rpc_response"] = _ms(start, end)

    timings["total"] = (
        timings["block_height"]
        + timings["peers"]
        + timings["rpc_response"]
    )
    return timings


async def run_benchmark() -> None:
    configs: List[NodeConfig] = load_nodes_config(NODES_CONFIG_PATH)
    if not configs:
        print("No nodes configured")
        return

    for cfg in configs:
        node = Node(name=cfg.name, rpc_url=cfg.rpc_url)
        timings = await benchmark_node(node)
        print(
            f"{node.name} - "
            f"block_height: {timings['block_height']:.0f}ms, "
            f"peers: {timings['peers']:.0f}ms, "
            f"rpc_response: {timings['rpc_response']:.0f}ms"
        )
        print(f"Total: {timings['total']:.0f}ms")
