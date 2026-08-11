import signal
import cherrypy
from collections.abc import Callable

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QGuiApplication
from loguru import logger

def run_signal_tether() -> None:
    """Make SIGTERM/SIGINT gracefully quit the Qt event loop.

    Qt's C++ event loop blocks Python's signal delivery. A QTimer that fires
    regularly forces a return to the Python interpreter, where pending signals
    are dispatched.
    """
    _heartbeat = QTimer()
    _heartbeat.start(200)                    # every 200 ms is enough
    _heartbeat.timeout.connect(lambda: None) # no-op; just wakes Python up

    def _quit(sig, _frame):
        logger.info("Signal {} received — requesting graceful shutdown", sig)
        cherrypy.engine.exit()  # stop the ingest server
        QGuiApplication.quit()

    signal.signal(signal.SIGTERM, _quit)
    signal.signal(signal.SIGINT, _quit)

    # caller must hold a reference or it is GC'd
    return _heartbeat