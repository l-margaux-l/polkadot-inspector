# Polkadot Network Inspector

Polkadot Network Inspector is a monitoring tool for checking the health and performance of nodes in the Polkadot ecosystem.  
It is aimed at DevOps engineers and blockchain teams who want to be sure their public RPC endpoints and parachain nodes are alive and healthy.

_Project status: Work in progress (Stage 1 — project initialization and basic scaffolding)._

## Goals

- Provide a lightweight tool to monitor the health of Polkadot and parachain nodes.  
- Collect core metrics such as block height, peers count, finality lag, and RPC response time.  
- Expose a clear health status that can be used for alerts (email, webhooks, logs).  
- Serve as a portfolio project demonstrating clean architecture and production-ready monitoring patterns.  

## Roadmap (high-level)

- **Foundation**: project setup, configuration, basic entrypoint, node and metrics models, simple RPC connection and first health metric (block height).  
- **Metrics collection**: peers count, time since last block, RPC response time, finality lag, aggregated health report and error handling.  
- **Data storage**: file-based logging, CSV export, optional SQLite database for historical metrics.  
- **Alerts and notifications**: alert rules, email alerts, Slack or Discord webhooks, alert logging.  
- **Monitoring loop and configuration**: main monitoring loop, graceful shutdown, configurable intervals and alert thresholds.  

## Tech stack

- Python 3.11+  
- substrate-interface for interacting with Substrate-based nodes (Polkadot and parachains).  
- aiohttp for asynchronous network calls.  
- requests for simple HTTP requests.  
- python-dotenv for environment-based configuration.  

## Current project structure

At this stage the project only contains the basic scaffolding:

- `main.py` — entrypoint for the inspector.  
- `config.py` — configuration and constants (RPC endpoint, poll interval, paths).  
- `requirements.txt` — project dependencies.  
- `.gitignore` — ignored files and folders.  
- `.env.example` — example environment file.  

The rest of the architecture (models, services, tests) will be introduced in the next stages.

## Getting started (short version)

1. Clone the repository and go into the project folder.  
2. Create and activate a virtual environment.  
3. Install dependencies using: `pip install -r requirements.txt`  
4. Run the current version using: `python main.py`  

At this stage, the script only prints basic configuration (RPC endpoint and poll interval).  
Monitoring logic and metrics collection will be implemented in upcoming stages.
