from __future__ import annotations


class Node:
    def __init__(self, name: str, rpc_url: str) -> None:
        self.name = name.strip()
        self.rpc_url = rpc_url.strip()