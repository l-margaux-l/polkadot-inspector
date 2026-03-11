# Polkadot Network Inspector

`Polkadot Network Inspector` is a monitoring tool for checking the health and performance of nodes in the Polkadot ecosystem. It collects health metrics, stores them for analysis, and exposes a simple HTTP API for external monitoring tools.

## Who is this for?

- **Node operators** who want a simple, scriptable way to check the health of their Polkadot nodes.
- **DevOps/SRE engineers** who need a small monitoring component that is easy to integrate with existing systems and can be shipped as a Docker container.
- **Blockchain developers** who want an example of a Python-based monitoring tool (async I/O, SQLite, FastAPI, Docker).

## What problems does it solve?

- Provides a single place to collect key health metrics from one or more Polkadot RPC endpoints.
- Helps detect degraded or stuck nodes (finality lag, time since last block, peers, RPC latency).
- Exposes machine-readable outputs (CSV, JSON, HTTP) that can be consumed by dashboards, alerting systems or other scripts.

## Features

- Health metrics per node:
   - block height
   - peers count
   - time since last block
   - RPC response time
   - finality lag
   - computed health status
- Periodic monitoring loop with configurable interval.
- Metrics storage in SQLite for historical analysis.
- CSV export for external analysis.
- Alerting hooks (email, Slack/webhook) — optional.
- HTTP health endpoint:
   - `/health` — liveness check
   - `/metrics` — latest metrics for all nodes as JSON
- Docker support to run the HTTP API in a container.

## Tech stack

- Python 3.12
- `substrate-interface` for talking to Polkadot RPC
- `aiohttp` for async HTTP calls
- `FastAPI` + `uvicorn` for the HTTP health API
- SQLite for metrics storage
- Docker for containerized deployment

## Installation

1. Clone the repository:
   - `git clone https://github.com/l-margaux-l/polkadot-inspector.git`
   - `cd polkadot-inspector`
2. Create and activate a virtual environment (optional but recommended).
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Set up environment variables (optional):
   - Copy `.env.example` to `.env` and adjust if needed.

## Configuration

Nodes are configured via `nodes_config.json` in the project root.

Basic example:
`[ { "name": "polkadot_main", "chain": "polkadot", "rpc_url": "https://rpc.polkadot.io" } ]`

You can add multiple entries to monitor several nodes.
Log and database paths are configured in `config.py` and can be overridden via environment variables if needed.

## Usage

### One-time metrics collection

Run a single health check for all configured nodes and print results to the console:

`python main.py --check-all-nodes`

This will:

- Load nodes from `nodes_config.json`
- Collect health metrics for each node
- Print a formatted table with statuses


### Continuous monitoring loop

Run the monitoring loop with a given interval (in seconds):

`python main.py --monitor --interval 30`

This will:

- Periodically collect metrics for all nodes
- Write metrics to log files and SQLite
- Send alerts to Slack for warning and critical conditions (if slack webhook url is added in `.env`)
- Send email alerts for critical conditions (if email settings are configured)

Stop with `Ctrl+C`.

### Status file for external tools

The monitoring loop can export a simple JSON status file (`status.json`) with the latest metrics snapshot. This file can be consumed by external monitoring systems or scripts.

Example structure:

`{ "last_update": "2026-03-10T14:30:00Z", "nodes": [ { "name": "polkadot_main", "status": "healthy", "block_height": 123456, "current_block_height": 123456, "peers_count": 42, "finality_lag": 0, "time_since_last_block": 6, "rpc_response_time": 150.0, "timestamp": "2026-03-10T14:29:55+00:00" } ] }`

### Daily / weekly statistics

The `services.statistics` module can generate aggregate reports, for example:

- Uptime percentage over the last N hours
- Average finality lag
- Average peers count
- Average RPC response time
- Number of incidents (warning/critical periods)

Run from the project root:

`python -c "from services.statistics import calculate_uptime, generate_daily_report; print(calculate_uptime('polkadot', hours=24)); print(generate_daily_report(hours=24))"`

### HTTP health API

Start the FastAPI server locally:

`uvicorn services.http_server:app --host 0.0.0.0 --port 8000`

You can call these endpoints from a browser or with curl, for example:
- `curl http://localhost:8000/health`
   - Returns a simple liveness JSON payload:
    `{"status": "ok", "timestamp": "..."}`
- `curl http://localhost:8000/metrics`
   - Returns the latest metrics for all nodes in JSON format.
   - If the metrics table is not initialized yet, returns a valid payload with an empty list of nodes.

### Other CLI options

Run `python main.py -h` to see all available commands and flags.


## Run with Docker

You can run the HTTP health API without installing Python or dependencies locally.

Build the image:

`docker build -t polkadot-inspector .`

Run the container:

`docker run --rm -p 8000:8000 polkadot-inspector`

Then you can use the same HTTP endpoints as in the local run:

- `curl http://localhost:8000/health`
- `curl http://localhost:8000/metrics`

If you want the container to use your existing local SQLite database:

`docker run --rm -p 8000:8000 -v "$(pwd)/db:/app/db" polkadot-inspector`

This mounts the local `db/` directory into the container so the HTTP API can see the same metrics data as your local monitoring loop.

## Development

Basic checks:
- Compile sources:
`python -m compileall .`

You can also use the benchmark mode to measure metric collection times:

`python main.py --benchmark`

This will print timings per metric and total per node.

## License

`MIT License`