from __future__ import annotations

import argparse
import asyncio
import signal

from config import NODES_CONFIG_PATH
from models.node import Node
from services.metrics_collector import get_block_height
from services.monitoring_loop import monitoring_loop
from services.logger import setup_logger
from services.nodes_config import NodeConfig, load_nodes_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="polkadot-inspector")
    parser.add_argument("--collect-block-height", action="store_true")
    parser.add_argument("--node", type=str, help="Node name from config")
    parser.add_argument("--all-nodes", action="store_true", help="Check all nodes")

    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Run continuous monitoring loop",
    )

    parser.add_argument(
        "--interval",
        type=int,
        help="Override monitoring interval in seconds",
    )

    return parser.parse_args()


async def shutdown_handler(loop: asyncio.AbstractEventLoop) -> None:
    logger = setup_logger()
    logger.info("Received shutdown signal, cancelling tasks")

    tasks: set[asyncio.Task] = {
        t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task(loop)
    }

    for task in tasks:
        task.cancel()

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("Shutdown complete, stopping event loop")
    loop.stop()


def setup_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(shutdown_handler(loop)),
        )


def select_nodes(all_nodes: list[NodeConfig], *, name_or_chain: str | None, check_all: bool) -> list[NodeConfig]:
    if check_all:
        return all_nodes
    if not name_or_chain:
        raise ValueError("--node is required unless --all-nodes is set")

    key = name_or_chain.strip().lower()
    by_name = [n for n in all_nodes if n.name.lower() == key]
    if by_name:
        return by_name

    by_chain = [n for n in all_nodes if n.chain.lower() == key]
    if len(by_chain) == 1:
        return by_chain
    if by_chain:
        raise ValueError(f"Ambiguous chain '{name_or_chain}': specify a node name instead")

    raise ValueError(f"Unknown node: {name_or_chain}")


async def collect_block_heights(nodes: list[NodeConfig]) -> list[tuple[NodeConfig, int]]:
    async def fetch(n: NodeConfig) -> tuple[NodeConfig, int]:
        node = Node(name=n.name, rpc_url=n.rpc_url)
        height = await get_block_height(node)
        return n, height

    results = await asyncio.gather(*(fetch(n) for n in nodes))
    return list(results)


def main() -> None:
    args = parse_args()

    if args.monitor:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        setup_signal_handlers(loop)

        try:
            loop.create_task(monitoring_loop(check_interval=args.interval))
            loop.run_forever()
        finally:
            loop.close()
        return

    if not args.collect_block_height:
        print("No action specified. Use --collect-block-height or --monitor")
        return

    if args.all_nodes and args.node:
        raise ValueError("Use either --node or --all-nodes, not both")

    nodes = load_nodes_config(NODES_CONFIG_PATH)
    selected = select_nodes(nodes, name_or_chain=args.node, check_all=args.all_nodes)
    heights = asyncio.run(collect_block_heights(selected))
    for node_cfg, height in heights:
        label = node_cfg.chain.capitalize() if args.node and args.node.strip().lower() == node_cfg.chain.lower() else node_cfg.name
        print(f"{label} block height: {height}")


if __name__ == "__main__":
    main()
