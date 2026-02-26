from __future__ import annotations

import argparse
import asyncio

from config import POLKADOT_RPC_URL
from models.node import Node
from services.metrics_collector import get_block_height


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="polkadot-inspector")
    parser.add_argument("--collect-block-height", action="store_true")
    parser.add_argument("--node", default="polkadot")
    return parser.parse_args()


def resolve_node(node_name: str) -> Node:
    key = node_name.strip().lower()
    if key != "polkadot":
        raise ValueError(f"Unknown node: {node_name}")
    return Node(name="Polkadot", rpc_url=POLKADOT_RPC_URL)


def main() -> None:
    args = parse_args()

    if args.collect_block_height:
        node = resolve_node(args.node)
        height = asyncio.run(get_block_height(node))
        print(f"{node.name} block height: {height}")
        return

    print("No action specified. Use --collect-block-height --node polkadot")


if __name__ == "__main__":
    main()