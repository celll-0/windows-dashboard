import os
import cherrypy
import threading
from typing import Dict

from .data import SnapshotStore
from .data.models import AccountSummary
from .control import ControlServer

from PyQt6.QtCore import QThread, pyqtSignal, QObject
from loguru import logger


class IngestServer(QObject):
    summaryRequestSucceeded = pyqtSignal(object)  # AccountSummary

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def summary(self):
        data: Dict[str, str] = cherrypy.request.json
        logger.info("Received summary data update request")
        try:
            summary = AccountSummary.from_dict(data)
            self.summaryRequestSucceeded.emit(summary)
            return {"success": True, "message": "Gui summary updated"}
        except Exception as e:
            logger.error("Failed to process summary data: {}", e)
            return {"success": False, "message": str(e)}

class IngestServerThread(QThread):
    summaryReady = pyqtSignal(object)  # AccountSummary
    stopRequested = pyqtSignal()
    restartRequested = pyqtSignal()
    refreshRequested = pyqtSignal()

    def __init__(self, store: SnapshotStore) -> None:
        super().__init__()
        self.setObjectName("ingest_server_thread")
        self._server = IngestServer()
        self._server.summaryRequestSucceeded.connect(self.summaryReady)
        self._control = ControlServer(store)
        self._control.stopRequested.connect(self.stopRequested)
        self._control.restartRequested.connect(self.restartRequested)
        self._control.refreshRequested.connect(self.refreshRequested)

    def run(self) -> None:
        """Run the ingest + control servers on one shared CherryPy engine."""
        threading.current_thread().name = QThread.currentThread().objectName()
        cherrypy.tree.mount(self._server, "/ingest", {"/": {}})
        cherrypy.tree.mount(self._control, "/control", {"/": {}})
        cherrypy.config.update({
            "global": {
                "server.socket_host": "0.0.0.0",
                "server.socket_port": int(os.getenv("GUI_PORT")),
                "server.socket_timeout": 3,
            },
        })
        cherrypy.engine.start()
        logger.info("Ingest/control server thread started")
        cherrypy.engine.block()
