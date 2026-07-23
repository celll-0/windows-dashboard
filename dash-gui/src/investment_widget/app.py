"""Composition root: builds every component and wires the signal flow.

    Poller --(AccountSummary)--> Application._on_summary
                                     |
                          SnapshotStore (persist + 24h baseline)
                                     |
                          build_view_model --> SummaryBridge --> QML
"""
from __future__ import annotations

import sys

from loguru import logger
from PyQt6.QtCore import QUrl, QObject
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

from .bridge import SummaryBridge
from .config import Config
from .data import AccountSummary, SnapshotStore
from .paths import MAIN_QML
from .ingest import IngestServerThread
from .presentation import build_view_model
from .services import WidgetBehaviour, FetchSummaryWorker, ApiClient


class Application:
    def __init__(self) -> None:
        logger.info("Initialising application")
        self._qt_app = QGuiApplication(sys.argv)

        self._config = Config.load()
        self._store = SnapshotStore(config=self._config)
        self._bridge = SummaryBridge()

        logger.debug("Loading QML: {}", MAIN_QML)
        self._engine = QQmlApplicationEngine()
        self._engine.rootContext().setContextProperty("bridge", self._bridge)
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
        logger.info(
            "Summary received | ts={}",
            summary.timestamp.isoformat(),
        )
        baseline = self._store.value_near_24h_ago()
        self._store.insert(summary.timestamp, summary.total_value)
        self._bridge.set_model(build_view_model(summary, baseline))

    def _on_error(self, message: str) -> None:
        logger.error("Event failed: {}", message)
        self._bridge.show_error(message)

    def run(self) -> int:
        logger.info("Entering Qt event loop")
        
        # Fetch immediately on launch
        self._fetch_summary_worker = FetchSummaryWorker(ApiClient(self._config.endpoint_url))
        self._fetch_summary_worker.succeeded.connect(self._on_summary)
        self._fetch_summary_worker.failed.connect(self._on_error)
        # self._fetch_summary_worker.finished.connect(self._fetch_summary_worker.deleteLater)
        
        # Start the ingest server in a separate thread to handle incoming summary updates
        self._ingest_server = IngestServerThread()
        self._ingest_server.summaryReady.connect(self._on_summary)

        self._ingest_server.start()
        # self._fetch_summary_worker.start()
        
        exit_code = self._qt_app.exec()
        logger.info("Qt event loop exited with code {}", exit_code)
        return exit_code
