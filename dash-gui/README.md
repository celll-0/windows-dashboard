# Investment Widget

A frameless, stay-on-bottom desktop widget that displays your investment account
summary. It polls a local HTTP endpoint (your Docker service) on an interval and
renders the result with a QML view driven by a Python bridge.

## Layout

```
investment-widget/
├── main.py                       # entry point (python main.py)
├── config.json                   # endpoint URL, poll interval, position
├── requirements.txt
└── src/investment_widget/
    ├── app.py                    # composition root — wires everything together
    ├── config.py                 # Config dataclass + load/save
    ├── paths.py                  # project paths in one place
    ├── domain/                   # pure entities (AccountSummary) — no Qt
    ├── data/                     # ApiClient (HTTP) + SnapshotStore (SQLite)
    ├── services/                 # Poller (timer + worker thread), WindowBehavour
    ├── presentation/             # formatting + AccountSummary → view-model dict
    ├── bridge/                   # SummaryBridge — the only Python object QML sees
    └── ui/                       # QML views (Main, PLColumn, MetricCard, StatItem)
```

## Architecture

```
Poller ──AccountSummary──▶ app._on_summary
                               │  persist + read 24h baseline (SnapshotStore)
                               ▼
                         build_view_model ──▶ SummaryBridge.model ──▶ QML
```

- **domain / data / presentation** are framework-light and unit-testable.
- **bridge** is the single QObject exposed to QML via `setContextProperty`.
- **ui** binds declaratively to `bridge.model`; no imperative layout code.

## Run

```bash
poetry install
poetry run python main.py
```

Edit `config.json` to point at your container:

```json
{
  "base_url": "http://example:{port}/api/v1",
  "poll_interval_seconds": 60,
  "position": { "x": 20, "y": 20 }
}
```

## Notes

- The endpoint returns numeric values (no currency symbol); the widget formats
  them as GBP for display.
- **Last 24h** and **ROR** are derived locally — they show `—` until the widget
  has been running long enough to have a snapshot from ~24h ago in `snapshots.db`.
