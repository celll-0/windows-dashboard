import os
import cherrypy
import threading
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

from .data import AccountSummary, OpenPositions, SnapshotStore
from .control import ControlServer
from .constants import DEFAULT_PORT

from PyQt6.QtCore import QThread, pyqtSignal, QObject
from loguru import logger


class UpdatePayload(BaseModel):
    """Schema for a POST /ingest/update body: {"type": ..., "data": {...}}."""
    type: str
    data: Dict[str, Any] = {}


class IngestServer(QObject):
    summaryRequestSucceeded = pyqtSignal(object)  # AccountSummary
    positionsRequestSucceeded = pyqtSignal(object)  # OpenPositions

    def __init__(self) -> None:
        super().__init__()
        self._handlers = {
            "AccountSummary": self._handle_summary,
            "OpenPositions": self._handle_positions,
        }

    def _check_token(self) -> bool:
        auth = cherrypy.request.headers.get("Authorization", "")
        expected = os.getenv("DAILYBRIEF_GUI_API_TOKEN")
        if not expected or auth != f"Bearer {expected}":
            logger.warning("Rejected ingest request with invalid/missing token")
            cherrypy.response.status = 401
            return False
        return True

    def _handle_summary(self, data: Dict[str, Any]) -> Dict:
        summary = AccountSummary.from_dict(data)
        self.summaryRequestSucceeded.emit(summary)
        return {"success": True, "message": "Gui summary updated"}

    def _handle_positions(self, data: Dict[str, Any]) -> Dict:
        positions = OpenPositions.from_dict(data)
        self.positionsRequestSucceeded.emit(positions)
        return {"success": True, "message": "Gui positions updated"}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def update(self):
        if not self._check_token():
            return {"success": False, "message": "Invalid or missing token"}
        try:
            payload = UpdatePayload.model_validate(cherrypy.request.json)
        except ValidationError as e:
            logger.warning("Received malformed update payload: {}", e)
            return {"success": False, "message": "Malformed payload"}

        handler = self._handlers.get(payload.type)
        if handler is None:
            logger.warning("Received update request with unknown type: {}", payload.type)
            return {"success": False, "message": f"Unknown type: {payload.type}"}
        logger.info("Received {} data update request", payload.type)
        try:
            return handler(payload.data)
        except Exception as e:
            logger.error("Failed to process {} data: {}", payload.type, e)
            return {"success": False, "message": str(e)}

class IngestServerThread(QThread):
    summaryReady = pyqtSignal(object)  # AccountSummary
    positionsReady = pyqtSignal(object)  # OpenPositions
    stopRequested = pyqtSignal()
    restartRequested = pyqtSignal()
    refreshRequested = pyqtSignal()

    def __init__(self, store: SnapshotStore) -> None:
        super().__init__()
        self.setObjectName("ingest_server_thread")
        self._server = IngestServer()
        self._server.summaryRequestSucceeded.connect(self.summaryReady)
        self._server.positionsRequestSucceeded.connect(self.positionsReady)
        self._control = ControlServer(store)
        self._control.stopRequested.connect(self.stopRequested)
        self._control.restartRequested.connect(self.restartRequested)
        self._control.refreshRequested.connect(self.refreshRequested)

    def run(self) -> None:
        """Run the ingest + control servers on one shared CherryPy engine."""
        threading.current_thread().name = QThread.currentThread().objectName()
        cherrypy.tree.mount(self._server, "/ingest", {"/": {}})
        cherrypy.tree.mount(self._control, "/control", {"/": {}})

        server_port = int(os.getenv("GUI_PORT", DEFAULT_PORT))
        cherrypy.config.update({
            "global": {
                "server.socket_host": "0.0.0.0",
                "server.socket_port": server_port,
                "server.socket_timeout": 3,
            },
        })
        cherrypy.engine.start()
        logger.info("Ingest/control server thread started")
        cherrypy.engine.block()
