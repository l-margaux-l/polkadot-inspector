from __future__ import annotations

import asyncio
from typing import Any

from substrateinterface import SubstrateInterface


async def connect_to_node(rpc_url: str) -> SubstrateInterface:
    """Create a SubstrateInterface connection to the given RPC URL."""
    rpc_url = rpc_url.strip()
    if not rpc_url:
        raise ValueError("rpc_url must not be empty")

    return await asyncio.to_thread(SubstrateInterface, url=rpc_url)


def get_chain_head(substrate: SubstrateInterface) -> dict[str, Any]:
    block_hash = substrate.get_chain_head()
    block_height = substrate.get_block_number(block_hash)
    return {"block_height": block_height, "block_hash": block_hash}