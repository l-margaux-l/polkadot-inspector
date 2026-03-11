from __future__ import annotations

import asyncio

from config import CHECK_INTERVAL, NODES_CONFIG_PATH
from models.node import Node
from models.metrics import HealthMetrics
from services.alerts import check_alerts
from services.alerts_logger import log_alert
from services.database import MetricsDB
from services.health_checker import collect_all_metrics
from services.logger import log_metrics, setup_logger
from services.slack_notifier import send_slack_alert
from services.email_notifier import send_email_alert
from services.nodes_config import load_nodes_config
from services.status_exporter import export_status_to_file


async def monitoring_loop(check_interval: int | None = None) -> None:
    logger = setup_logger()
    db = MetricsDB()
    db.create_tables()

    interval = check_interval or CHECK_INTERVAL

    while True:
        nodes = load_nodes_config(NODES_CONFIG_PATH)
        iteration_metrics: list[HealthMetrics] = []
        for node_cfg in nodes:
            node = Node(name=node_cfg.name, rpc_url=node_cfg.rpc_url)
            logger.info(
                "Collecting metrics",
                extra={"extra_data": {"node_name": node.name}},
            )

            metrics = await collect_all_metrics(node)
            log_metrics(metrics)
            await db.insert_metrics(metrics)
            iteration_metrics.append(metrics)

            alerts = check_alerts(metrics)
            for alert in alerts:
                log_alert(alert)
                await send_slack_alert(alert)
                await send_email_alert(alert)

        if iteration_metrics:
            export_status_to_file(iteration_metrics)

        print("Iteration done, sleeping...", interval)
        await asyncio.sleep(interval)