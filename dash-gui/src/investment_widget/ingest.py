import os
import cherrypy
import threading
from typing import Dict

from .data.models import AccountSummary

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

    def __init__(self, ) -> None:
        super().__init__()
        self.setObjectName("ingest_server_thread")
        self._server = IngestServer()
        self._server.summaryRequestSucceeded.connect(self.summaryReady)

    def run(self) -> None:
        """Run the ingest server for income summary push updates"""
        threading.current_thread().name = QThread.currentThread().objectName()
        cherrypy.quickstart(
            self._server,
            "/ingest",
            {
                'global': {'server.socket_host': '0.0.0.0', 'server.socket_port': int(os.getenv("GUI_PORT")), 'server.socket_timeout': 3},
                "/": {},
            },
        )
        logger.info(f"Ingest server thread started")
