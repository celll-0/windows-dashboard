# Dashboard

A personal investment dashboard: a Docker-hosted backend service that fetches Trading212 account data on a schedule and a frameless PyQt6/QML desktop widget that displays it.

## Architecture

```
┌─────────────────────────────────┐        ┌───────────────────────────────┐
│  dash-services  (Docker)        │        │  dash-gui  (local)            │
│                                 │        │                               │
│  Scheduler ──▶ Trading212 API   │─push──▶│  IngestServer (CherryPy)      │
│       │                         │        │       │                       │
│       ▼                         │        │       ▼ (Qt signal)           │
│  store.json  (JsonPersistence)  │        │  SummaryBridge ──▶ QML view   │
│       │                         │        │                               │
│  CherryPy /api/v1/summary  ◀───pull──────│  Poller (hourly fallback)     │
└─────────────────────────────────┘        └───────────────────────────────┘
```

**dash-services** fetches the Trading212 account summary at key market times (LDN/NY open and close) and persists it to `store.json`. After each fetch it pushes the payload to the GUI's ingest endpoint. It also exposes `GET /api/v1/summary` as a pull fallback.

**dash-gui** runs a small ingest server (CherryPy) to receive pushed updates and falls back to polling the services endpoint hourly. The Python bridge (`SummaryBridge`) feeds data into QML. A SQLite snapshot store tracks the 24 h baseline for P&L and ROR calculations.

## Prerequisites

- Python 3.12+
- Poetry
- Docker + Docker Compose

## Setup

```bash
poetry install
cp .env.example .env  # fill in credentials
```

## Environment

Create a `.env` at the project root:

```dotenv
SERVICES_PORT=<port>
GUI_PORT=<port>
GUI_HOST=<host>

TRADING212_AUTH_KEY=<your key>
TRADING212_KEY_ID=<your key id>
TRADING212_BASE_URL=<base url>
```

Trading212 API credentials and base URL: https://docs.trading212.com/api/accounts/getaccountsummary

## Running

```bash
# Start both components (services in background, GUI in foreground)
./start.sh
```

Or separately:

```bash
docker compose up -d   # services only
./run-gui.sh           # GUI only
./stop-services.sh     # stop services container
```

## Default fetch schedule

The backend fetches on startup and then at these times (London):

| Time  | Event            |
|-------|------------------|
| 07:30 | Before LDN open  |
| 08:30 | After LDN open   |
| 14:00 | NY market open   |
| 16:30 | LDN market close |
| 21:30 | NY market close  |
