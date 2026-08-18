"""Composition root: builds every component and wires the signal flow.

    Poller --(AccountSummary)--> Application._on_summary
                                     |
                          SnapshotStore (persist + 24h baseline)
                                     |
                          build_view_model --> SummaryBridge --> QML
"""
from __future__ import annotations

import os
import subprocess
import sys

import cherrypy
from loguru import logger
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

from .bridge import WidgetBridge
from .config import Config
from .constants import ANIMATION_DURATION_MS
from .data import AccountSummary, NewsFeed, OpenPositions, SnapshotStore
from .paths import MAIN_QML
from .presentation import build_view_model, build_positions_view_model, build_news_feed_view_model
from .services import WidgetBehaviour, FetchInvestmentsDataWorker, ApiClient
from .ingest import IngestServerThread


class Application:
    def __init__(self) -> None:
        logger.info("Initialising application")
        self._qt_app = QGuiApplication(sys.argv)

        self._config = Config.load()
        self._store = SnapshotStore(config=self._config)
        self._bridge = WidgetBridge()
        self._api_client = ApiClient(self._config.base_url)

        logger.debug("Loading QML")
        self._engine = QQmlApplicationEngine()
        self._engine.rootContext().setContextProperty("bridge", self._bridge)
        self._engine.rootContext().setContextProperty("animationDurationMs", ANIMATION_DURATION_MS)
        self._engine.load(QUrl.fromLocalFile(str(MAIN_QML)))
        if not self._engine.rootObjects():
            logger.critical("Failed to load QML: {}", MAIN_QML)
            raise RuntimeError(f"Failed to load QML: {MAIN_QML}")
        logger.info("QML loaded successfully")

        self._window = self._engine.rootObjects()[0]
        self._position_window()
        self._widget_behaviour_manager = WidgetBehaviour(self._window)
        logger.info("Application initialised")

    def _position_window(self) -> None:
        pos = self._config.position
        self._window.setProperty("x", pos["x"])
        self._window.setProperty("y", pos["y"])
        logger.debug("Window positioned at ({}, {})", pos["x"], pos["y"])

    def _on_summary(self, summary: AccountSummary) -> None:
        try:
            logger.info(
                "Summary received | ts={}",
                summary.timestamp.isoformat(),
            )
            baseline = self._store.value_near_24h_ago()
            self._store.insert(summary.timestamp, summary.total_value)
            self._bridge.set_model(build_view_model(summary, baseline))
        except Exception as e:
            logger.error("Widget could not load summary: {}", e)

    def _on_positions(self, open_positions: OpenPositions) -> None:
        try:
            logger.info(
                "Positions received | ts={}",
                open_positions.timestamp.isoformat(),
            )
            self._bridge.set_positions(build_positions_view_model(open_positions.positions))
        except Exception as e:
            logger.error("Widget could not load positions: {}", e)
    
    def _on_news_feed(self, feed: NewsFeed) -> None:
        try:
            logger.info("News feed received | items={}", len(feed.items))
            self._bridge.set_news_feed(build_news_feed_view_model(feed))
        except Exception as e:
            logger.error("Widget could not load news feed: {}", e)

    def _on_error(self, message: str) -> None:
        logger.error("Event failed: {}", message)
        self._bridge.show_error(message)

    def _on_stop_requested(self) -> None:
        logger.info("Stop requested via control API")
        cherrypy.engine.exit()
        self._qt_app.quit()

    def _on_restart_requested(self) -> None:
        logger.info("Restart requested via control API — relaunching")
        env = os.environ.copy()
        if getattr(sys, "frozen", False):
            # Force production path resolution regardless of what this
            # process's own environment happened to inherit (e.g. a stray
            # ENV=development from .env if launched via `dailybrief start`) --
            # a frozen relaunch must never resolve paths as if it were a dev
            # checkout. See ROOT_DIR in paths.py.
            env["ENV"] = "production"
        subprocess.Popen(
            [sys.executable, *sys.argv],
            env=env,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
        )
        self._on_stop_requested()

    def _on_fresh_data(self, datapoint: str, data: object) -> None:
        if not data or data is None:
            logger.warning("Received empty data for datapoint '{}'", datapoint)
            return

        if datapoint == "summary" and isinstance(data, AccountSummary):
            self._on_summary(data)
        elif datapoint == "positions" and isinstance(data, OpenPositions):
            self._on_positions(data)
        elif datapoint == "news_feed" and isinstance(data, NewsFeed):
            self._on_news_feed(data)
        else:
            logger.warning("Received unexpected data type for datapoint '{}': {}", datapoint, type(data))
            
    def _on_refresh_requested(self) -> None:
        logger.info("Refresh requested via control API")
        worker = FetchInvestmentsDataWorker(self._api_client, ["summary", "positions", "news_feed"])
        worker.succeeded.connect(self._on_fresh_data)
        worker.failed.connect(lambda datapoint, message: self._on_error(message))
        worker.finished.connect(worker.deleteLater)
        worker.start()
        self._refresh_worker = worker  # keep a reference so it isn't GC'd mid-run

    def run(self) -> int:
        logger.info("Entering Qt event loop")

        # Start the ingest/control server in a separate thread. Data refresh
        # is manual-only (triggered via the control API's `refresh`, see
        # `_on_refresh_requested`) -- no fetch happens automatically here.
        self._ingest_server = IngestServerThread(self._store)
        self._ingest_server.summaryReady.connect(self._on_summary)
        self._ingest_server.positionsReady.connect(self._on_positions)
        self._ingest_server.newsFeedReady.connect(self._on_news_feed)
        self._ingest_server.stopRequested.connect(self._on_stop_requested)
        self._ingest_server.restartRequested.connect(self._on_restart_requested)
        self._ingest_server.refreshRequested.connect(self._on_refresh_requested)

        self._ingest_server.start()

        exit_code = self._qt_app.exec()
        logger.info("Qt event loop exited with code {}", exit_code)
        return exit_code
