from __future__ import annotations

import asyncio

from models.node import Node
from services.rpc_client import connect_to_node, get_chain_head


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