from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage
from typing import List

from config import EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO, SMTP_PORT, SMTP_SERVER
from services.alerts import Alert, ALERT_LEVEL_CRITICAL


def _build_smtp_message(subject: str, body: str, recipients: List[str]) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)
    return msg


def _send_via_smtp(msg: EmailMessage) -> None:
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        if EMAIL_FROM and EMAIL_PASSWORD:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)


async def send_email_alert(alert: Alert, recipients: List[str] | None = None) -> None:
    if alert.level != ALERT_LEVEL_CRITICAL:
        return

    targets = recipients or ([EMAIL_TO] if EMAIL_TO else [])
    if not targets:
        return

    subject = "[CRITICAL] Polkadot Node Down"
    body = (
        f"Time: {alert.timestamp.isoformat()}\n"
        f"Level: {alert.level}\n"
        f"Message: {alert.message}\n"
    )

    msg = _build_smtp_message(subject, body, targets)
    await asyncio.to_thread(_send_via_smtp, msg)


async def send_daily_report(email: str) -> None:
    subject = "[REPORT] Polkadot Node Daily Health Summary"
    body = "Daily report feature is not implemented yet."
    msg = _build_smtp_message(subject, body, [email])
    await asyncio.to_thread(_send_via_smtp, msg)
