from __future__ import annotations

import argparse
import asyncio
import signal

from config import NODES_CONFIG_PATH, DATA_DIR
from models.node import Node
from models.metrics import HealthMetrics
from services.health_checker import collect_all_metrics
from services.alerts import check_alerts
from services.metrics_collector import get_block_height
from services.monitoring_loop import monitoring_loop
from services.logger import setup_logger
from services.nodes_config import NodeConfig, load_nodes_config
from services.database import MetricsDB
from services.csv_exporter import export_metrics_to_csv
from services.console_printer import print_metrics_table
from services.metrics_benchmark import run_benchmark


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

    parser.add_argument(
        "--check-node",
        type=str,
        help="Run one-off health check for a single node by name",
    )

    parser.add_argument(
        "--check-all-nodes",
        action="store_true",
        help="Run one-off health check for all configured nodes",
    )

    parser.add_argument(
        "--history",
        type=str,
        help="Show metrics history for a node by name",
    )

    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="How many past hours to include in history (default: 24)",
    )

    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export history to CSV file instead of printing to stdout",
    )

    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run benchmark mode to test metrics collection timings",
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


def _format_health_line(node_name: str, metrics_status: str, alerts_count: int) -> str:
    return f"{node_name:15} | {metrics_status:8} | alerts: {alerts_count}"


async def _check_single_node(node_name: str) -> None:
    logger = setup_logger()
    nodes = load_nodes_config(NODES_CONFIG_PATH)
    target = next((n for n in nodes if n.name == node_name), None)
    if target is None:
        print(f"Node '{node_name}' not found in config")
        return

    node = Node(name=target.name, rpc_url=target.rpc_url)
    logger.info("Running manual health check", extra={"extra_data": {"node_name": node.name}})

    metrics = await collect_all_metrics(node)
    alerts = check_alerts(metrics)

    print("=== Node health report ===")
    print(f"Node: {node.name}")
    print(f"Status: {metrics.status}")
    print(f"Block height: {metrics.block_height}")
    print(f"Peers: {metrics.peers_count}")
    print(f"Finality lag: {metrics.finality_lag}")
    print(f"RPC response time: {metrics.rpc_response_time} ms")
    print(f"Time since last block: {metrics.time_since_last_block} s")
    print()
    if alerts:
        print("Alerts:")
        for alert in alerts:
            print(f"- [{alert.level}] {alert.message}")
    else:
        print("Alerts: none")


async def _check_all_nodes() -> None:
    logger = setup_logger()
    nodes = load_nodes_config(NODES_CONFIG_PATH)
    if not nodes:
        print("No nodes configured")
        return

    metrics_list: list[HealthMetrics] = []

    for cfg in nodes:
        node = Node(name=cfg.name, rpc_url=cfg.rpc_url)
        logger.info(
            "Running manual health check (all nodes)",
            extra={"extra_data": {"node_name": node.name}},
        )

        metrics = await collect_all_metrics(node)
        metrics_list.append(metrics)

    print_metrics_table(metrics_list)


def _print_history_csv(metrics_list: list) -> None:
    print(
        "timestamp,node_name,block_height,current_block_height,"
        "peers_count,finality_lag,time_since_last_block,rpc_response_time,status"
    )
    for m in metrics_list:
        print(
            f"{m.timestamp.isoformat()},"
            f"{m.node_name},"
            f"{m.block_height or ''},"
            f"{m.current_block_height or ''},"
            f"{m.peers_count or ''},"
            f"{m.finality_lag or ''},"
            f"{m.time_since_last_block or ''},"
            f"{m.rpc_response_time or ''},"
            f"{m.status}"
        )


def _history_csv_path(node_name: str) -> str:
    from pathlib import Path

    base = Path(DATA_DIR)
    base.mkdir(parents=True, exist_ok=True)
    safe_name = node_name.replace(" ", "_")
    return str(base / f"history_{safe_name}.csv")


def _show_history(node_name: str, hours: int, export_csv: bool) -> None:
    db = MetricsDB()
    metrics_list = db.get_metrics_for_node(node_name=node_name, hours=hours)

    if not metrics_list:
        print(f"No metrics found for node '{node_name}' in the last {hours} hours")
        return

    if export_csv:
        filename = _history_csv_path(node_name)
        export_metrics_to_csv(metrics_list, filename)
        print(f"History exported to {filename}")
    else:
        _print_history_csv(metrics_list)


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

    if args.benchmark:
        asyncio.run(run_benchmark())
        return

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

    if args.check_node:
        asyncio.run(_check_single_node(args.check_node))
        return

    if args.check_all_nodes:
        asyncio.run(_check_all_nodes())
        return

    if args.history:
        _show_history(args.history, args.hours, args.export_csv)
        return

    if not args.collect_block_height:
        print(
            "No action specified. Use "
            "--collect-block-height, --check-node, --check-all-nodes, "
            "--history or --monitor"
        )
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
