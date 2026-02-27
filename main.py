from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from config import NODES_CONFIG_PATH
from models.node import Node
from services.metrics_collector import get_block_height


@dataclass(frozen=True, slots=True)
class NodeConfig:
    name: str
    chain: str
    rpc_url: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="polkadot-inspector")
    parser.add_argument("--collect-block-height", action="store_true")
    parser.add_argument("--node", type=str, help="Node name from config")
    parser.add_argument("--all-nodes", action="store_true", help="Check all nodes")
    return parser.parse_args()


def load_nodes_config(path: Path) -> list[NodeConfig]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    nodes = raw.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("Invalid nodes_config.json: 'nodes' must be a list")

    parsed: list[NodeConfig] = []
    for item in nodes:
        if not isinstance(item, dict):
            raise ValueError("Invalid nodes_config.json: each node must be an object")
        name = str(item.get("name", "")).strip()
        chain = str(item.get("chain", "")).strip()
        rpc_url = str(item.get("rpc_url", "")).strip()
        if not name or not chain or not rpc_url:
            raise ValueError("Invalid nodes_config.json: node requires name, chain, rpc_url")
        parsed.append(NodeConfig(name=name, chain=chain, rpc_url=rpc_url))

    return parsed


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

    if not args.collect_block_height:
        print("No action specified. Use --collect-block-height")
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
