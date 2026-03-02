from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from config import DATA_DIR
from models.metrics import HealthMetrics


class MetricsDB:
    def __init__(self, db_path: str | None = None) -> None:
        base_dir = Path(DATA_DIR)
        base_dir.mkdir(parents=True, exist_ok=True)
        if db_path is None:
            db_path = str(base_dir / "metrics.db")
        self._path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    node_name TEXT NOT NULL,
                    block_height INTEGER,
                    current_block_height INTEGER,
                    peers_count INTEGER,
                    finality_lag INTEGER,
                    time_since_last_block INTEGER,
                    rpc_response_time REAL,
                    status TEXT
                )
                """
            )
            conn.commit()

    async def insert_metrics(self, metrics: HealthMetrics) -> None:
        def _insert() -> None:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO metrics (
                        timestamp,
                        node_name,
                        block_height,
                        current_block_height,
                        peers_count,
                        finality_lag,
                        time_since_last_block,
                        rpc_response_time,
                        status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        metrics.timestamp.isoformat(),
                        metrics.node_name,
                        metrics.block_height,
                        metrics.current_block_height,
                        metrics.peers_count,
                        metrics.finality_lag,
                        metrics.time_since_last_block,
                        metrics.rpc_response_time,
                        metrics.status,
                    ),
                )
                conn.commit()

        await asyncio.to_thread(_insert)

    def get_metrics_for_node(self, node_name: str, hours: int = 24) -> List[HealthMetrics]:
        since = datetime.utcnow() - timedelta(hours=hours)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT
                    timestamp,
                    node_name,
                    block_height,
                    current_block_height,
                    peers_count,
                    finality_lag,
                    time_since_last_block,
                    rpc_response_time,
                    status
                FROM metrics
                WHERE node_name = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                """,
                (node_name, since.isoformat()),
            )
            rows = cursor.fetchall()

        results: List[HealthMetrics] = []
        for row in rows:
            ts = datetime.fromisoformat(row["timestamp"])
            def _to_int(value: object) -> int | None:
                return int(value) if value is not None else None

            def _to_float(value: object) -> float | None:
                return float(value) if value is not None else None

            metrics = HealthMetrics(
                node_name=row["node_name"],
                timestamp=ts,
                block_height=_to_int(row["block_height"]),
                current_block_height=_to_int(row["current_block_height"]),
                peers_count=_to_int(row["peers_count"]),
                finality_lag=_to_int(row["finality_lag"]),
                time_since_last_block=_to_int(row["time_since_last_block"]),
                rpc_response_time=_to_float(row["rpc_response_time"]),
                status=row["status"],
            )
            results.append(metrics)

        return results