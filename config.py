from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

POLKADOT_RPC_URL: str = os.getenv(
    "POLKADOT_RPC_URL",
    "wss://polkadot.api.onfinality.io/public-ws",
)

# Basic monitoring defaults
DEFAULT_POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

# Logging paths 
LOGS_DIR: str = os.getenv("LOGS_DIR", "logs")
DATA_DIR: str = os.getenv("DATA_DIR", "data")
