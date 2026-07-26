"""Local control API: stop/restart/refresh the widget, list stored snapshots.

Mounted alongside the ingest server (see `ingest.py`) on the same CherryPy
engine/port. Routes are gated by a shared-secret token since that port must
stay bound to 0.0.0.0 for dash-services (in Docker) to reach it -- see
`ingest.py` for why loopback-only isn't an option here.
"""
from __future__ import annotations

import os
from datetime import datetime

import cherrypy
from PyQt6.QtCore import QObject, pyqtSignal
from loguru import logger

from .data import SnapshotStore


class ControlServer(QObject):
    stopRequested = pyqtSignal()
    restartRequested = pyqtSignal()
    refreshRequested = pyqtSignal()

    def __init__(self, store: SnapshotStore) -> None:
        super().__init__()
        self._store = store

    def _check_token(self) -> bool:
        token = cherrypy.request.headers.get("X-Kel-Dash-Token")
        expected = os.getenv("KEL_DASH_CONTROL_TOKEN")
        if not expected or token != expected:
            logger.warning("Rejected control request with invalid/missing token")
            cherrypy.response.status = 401
            return False
        return True

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def stop(self):
        if not self._check_token():
            return {"success": False, "message": "Invalid or missing token"}
        logger.info("Control API: stop requested")
        self.stopRequested.emit()
        return {"success": True, "message": "Stop requested"}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def restart(self):
        if not self._check_token():
            return {"success": False, "message": "Invalid or missing token"}
        logger.info("Control API: restart requested")
        self.restartRequested.emit()
        return {"success": True, "message": "Restart requested"}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def refresh(self):
        if not self._check_token():
            return {"success": False, "message": "Invalid or missing token"}
        logger.info("Control API: refresh requested")
        self.refreshRequested.emit()
        return {"success": True, "message": "Refresh requested"}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def snapshots(self, since: str | None = None):
        if not self._check_token():
            return {"success": False, "message": "Invalid or missing token"}
        since_dt = datetime.fromisoformat(since) if since else None
        return {"success": True, "snapshots": self._store.list_snapshots(since_dt)}
