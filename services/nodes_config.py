from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True, slots=True)
class NodeConfig:
    name: str
    chain: str
    rpc_url: str


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