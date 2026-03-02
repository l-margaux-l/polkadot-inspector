from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


PROJECT_ROOT: Path = Path(__file__).resolve().parent

NODES_CONFIG_PATH: Path = Path(os.getenv("NODES_CONFIG_PATH", str(PROJECT_ROOT / "nodes_config.json")))

POLKADOT_RPC_URL: str = os.getenv("POLKADOT_RPC_URL", "wss://polkadot.api.onfinality.io/public-ws")

DEFAULT_POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

LOGS_DIR: str = os.getenv("LOGS_DIR", "logs")
DATA_DIR: str = os.getenv("DATA_DIR", "data")

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")