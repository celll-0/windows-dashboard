"""Manual on-demand fetching of investments data (triggered via the control
API's `refresh` route -- see `Application._on_refresh_requested`).

One worker fetches a list of datapoints (e.g. "summary", "positions") on a
QThread so the UI thread never blocks. Each datapoint's endpoint path and
parser is looked up from `_DATAPOINTS`; results are surfaced per-datapoint as
Qt signals carrying a parsed domain object (or an error string), so one
failing datapoint doesn't block the others from updating.
"""
from __future__ import annotations

import threading
from typing import Callable

from loguru import logger
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from ..constants import _PROVIDER_ENDPOINTS
from ..data import AccountSummary, NewsFeed, OpenPositions
from .api_client import ApiClient


def _parse_summary(data: dict) -> AccountSummary:
    return AccountSummary.from_dict(data["summary"])


def _parse_positions(data: dict) -> OpenPositions:
    return OpenPositions.from_dict(data["positions"])


def _parse_news_feed(data: dict) -> NewsFeed:
    return NewsFeed.from_dict(data["news_feed"])


_DATAPOINTS: dict[str, tuple[str, Callable[[dict], object]]] = {
    "summary": (_PROVIDER_ENDPOINTS.investments.summary, _parse_summary),
    "positions": (_PROVIDER_ENDPOINTS.investments.positions, _parse_positions),
    "news_feed": (_PROVIDER_ENDPOINTS.news.feed, _parse_news_feed),
}


class FetchInvestmentsDataWorker(QThread):
    succeeded = pyqtSignal(str, object)  # datapoint name, parsed domain object
    failed = pyqtSignal(str, str)  # datapoint name, error message
    finished = pyqtSignal()

    def __init__(self, client: ApiClient, datapoints: list[str], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._client = client
        self._datapoints = datapoints
        self.setObjectName("Fetch_investments_data_worker")

    def run(self) -> None:
        threading.current_thread().name = QThread.currentThread().objectName()
        logger.debug("Fetch worker started | datapoints={}", self._datapoints)
        for datapoint in self._datapoints:
            entry = _DATAPOINTS.get(datapoint)
            if entry is None:
                logger.warning("Unknown datapoint requested: {}", datapoint)
                self.failed.emit(datapoint, f"Unknown datapoint: {datapoint}")
                continue

            endpoint, parse = entry
            try:
                parsed = parse(self._client.fetch(endpoint))
                logger.debug("Datapoint '{}' fetched successfully", datapoint)
                self.succeeded.emit(datapoint, parsed)
            except Exception as exc:  # noqa: BLE001 - surfaced to the UI as text
                logger.opt(exception=True).warning("Fetching datapoint '{}' failed: {}", datapoint, exc)
                self.failed.emit(datapoint, str(exc))
        self.finished.emit()
