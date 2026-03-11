from __future__ import annotations

import asyncio
from typing import Final

import requests

from config import SLACK_WEBHOOK_URL
from services.alerts import (
    Alert,
    ALERT_LEVEL_CRITICAL,
    ALERT_LEVEL_INFO,
    ALERT_LEVEL_WARNING,
)

LEVEL_EMOJI: Final[dict[str, str]] = {
    ALERT_LEVEL_INFO: "🟢",
    ALERT_LEVEL_WARNING: "🟡",
    ALERT_LEVEL_CRITICAL: "🔴",
}


async def send_slack_alert(alert: Alert) -> None:
    if not SLACK_WEBHOOK_URL:
        return

    emoji = LEVEL_EMOJI.get(alert.level, LEVEL_EMOJI[ALERT_LEVEL_INFO])
    title = f"Node alert ({alert.level})"
    ts = alert.timestamp.isoformat()

    payload = {
        "text": f"{emoji} {alert.message}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{title}*\n"
                        f"Node: `{alert.node_name}`\n"
                        f"Time: `{ts}`\n"
                        f"Level: `{alert.level}`\n"
                        f"{emoji} {alert.message}"
                    ),
                },
            },
        ],
    }

    def _post() -> None:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        response.raise_for_status()

    await asyncio.to_thread(_post)