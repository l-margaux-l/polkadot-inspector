from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

from models.metrics import HealthMetrics
from services.database import MetricsDB


app = FastAPI(title="Polkadot Inspector Health API")


class NodeMetricsResponse(BaseModel):
    name: str
    status: str
    block_height: int | None
    current_block_height: int | None
    peers_count: int | None
    finality_lag: int | None
    time_since_last_block: int | None
    rpc_response_time: float | None
    timestamp: datetime


class MetricsResponse(BaseModel):
    last_update: datetime
    nodes: List[NodeMetricsResponse]


def _load_latest_metrics() -> List[HealthMetrics]:
    db = MetricsDB()
    return db.get_latest_metrics_for_all_nodes()


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc),
    }


@app.get("/metrics", response_model=MetricsResponse)
def get_metrics() -> MetricsResponse:
    metrics_list = _load_latest_metrics()
    if not metrics_list:
        return MetricsResponse(last_update=datetime.now(timezone.utc), nodes=[])

    last_update = max(m.timestamp for m in metrics_list)
    nodes = [
        NodeMetricsResponse(
            name=m.node_name,
            status=m.status,
            block_height=m.block_height,
            current_block_height=m.current_block_height,
            peers_count=m.peers_count,
            finality_lag=m.finality_lag,
            time_since_last_block=m.time_since_last_block,
            rpc_response_time=m.rpc_response_time,
            timestamp=m.timestamp,
        )
        for m in metrics_list
    ]
    return MetricsResponse(last_update=last_update, nodes=nodes)
