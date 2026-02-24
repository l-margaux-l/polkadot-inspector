from __future__ import annotations

from config import POLKADOT_RPC_URL, DEFAULT_POLL_INTERVAL_SECONDS


def main() -> None:
    """Entry point for Polkadot Network Inspector."""
    print("Polkadot Network Inspector")
    print(f"Using RPC endpoint: {POLKADOT_RPC_URL}")
    print(f"Default poll interval: {DEFAULT_POLL_INTERVAL_SECONDS} seconds")
    print("Monitoring logic will be implemented in the next steps.")


if __name__ == "__main__":
    main()