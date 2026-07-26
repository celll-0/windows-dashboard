"""Local SQLite store of total-value snapshots.

The endpoint does not provide "Last 24h" or "ROR", so we persist a timestamped
total-value series and derive those by comparing against the row nearest to
24 hours ago.
"""
from __future__ import annotations

import sqlite3
from ..config import Config
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from loguru import logger

from ..paths import DB_PATH
from ..constants import SNAPSHOT_RETENTION_HOURS


class SnapshotStore:
    def __init__(self, config: Config, db_path=DB_PATH) -> None:
        self._db_path = db_path
        self._ensure_schema()
        self.timezone = config.timezone

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _ensure_schema(self) -> None:
        logger.debug("Ensuring snapshot schema at {}", self._db_path)
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS snapshots ("
                "id INTEGER PRIMARY KEY, ts TEXT NOT NULL, total_value REAL NOT NULL)"
            )

    def insert(self, ts: datetime, total_value: float) -> None:
        logger.debug("Inserting snapshot | ts={}", ts.isoformat())
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO snapshots (ts, total_value) VALUES (?, ?)",
                (ts.isoformat(), total_value),
            )
            self.remove_old_snapshots(conn, ts)
    
    def remove_old_snapshots(self,
        conn: sqlite3.Connection | None = None,
        ts: datetime | None = None,
    ) -> None:
        """Remove snapshots older than the specified number of hours."""
        ts = ts or datetime.now(tz=ZoneInfo(self.timezone))
        cutoff = (ts - timedelta(hours=SNAPSHOT_RETENTION_HOURS)).isoformat()
        if conn is None:
            conn = self._connect()
        conn.execute("DELETE FROM snapshots WHERE ts < ?", (cutoff,))
        logger.debug("Removed snapshots older than {} hours", SNAPSHOT_RETENTION_HOURS)

    def list_snapshots(self, since: datetime | None = None) -> list[dict]:
        """All snapshots, oldest first, optionally restricted to `ts >= since`."""
        query = "SELECT ts, total_value FROM snapshots"
        params: tuple = ()
        if since is not None:
            query += " WHERE ts >= ?"
            params = (since.isoformat(),)
        query += " ORDER BY ts"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [{"ts": ts, "total_value": total_value} for ts, total_value in rows]

    def value_near_24h_ago(self) -> float | None:
        """Total value of the snapshot closest to 24h ago, or None if empty."""
        target = (datetime.now(tz=ZoneInfo(self.timezone)) - timedelta(hours=24)).isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT total_value FROM snapshots "
                "ORDER BY ABS(JULIANDAY(ts) - JULIANDAY(?)) LIMIT 1",
                (target,),
            ).fetchone()
        baseline = row[0] if row else None
        if baseline is None:
            logger.debug("No 24h baseline available yet")
        else:
            logger.debug("24h baseline: {:.2f}", baseline)
        return baseline
