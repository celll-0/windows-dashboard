import signal
import cherrypy
import threading
from os import getenv
from typing import Union
from loguru import logger

from .services import (
    StoreLike, PersistenceService
)
from .constants import (
    SERVICES_PORT,
    SERVER_HOST,
    SERVICES_DEFAULT_PORT
)


class DailyBriefServer(object):
    _data_client: StoreLike = PersistenceService
    _server_host: str = SERVER_HOST
    _server_port: int = SERVICES_PORT 
    _server_thread: Union[threading.Thread, None] = None

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        return {"message": "Dash Data Provider Server is running!"}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def summary(self):
        investments_data = self._data_client.get_from_table('investments')
        return {"summary": investments_data.get("summary", {})}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def positions(self):
        investments_data = self._data_client.get_from_table('investments')
        return {"positions": investments_data.get("positions", {})}


    
    def __init__(self):
        cherrypy.server.socket_host = self._server_host
        cherrypy.server.socket_port = self._server_port
        logger.debug("server initialised on host {} and port {}", self._server_host, self._server_port)
        if cherrypy.server.socket_port == SERVICES_DEFAULT_PORT:
            logger.warning(
                f"Dashboard Data Server is running on default port {SERVICES_DEFAULT_PORT}. This may cause "
                f"conflicts with other applications. Check port in the .env file."
            )
        
        cherrypy.server.socket_timeout = 3
        cherrypy.engine.autoreload.unsubscribe()


    def init_server_thread(self) -> tuple[threading.Thread, threading.Event]:
        server_thread = threading.Thread(
            target=lambda: self._run_server(),
            daemon=True, 
            name="DBF-main-server-thread",
        )
        shutdown_event = threading.Event()

        self._server_thread = server_thread
        self._shutdown_event = shutdown_event
        # Trigger a clean application shutdown when cherrypy engine recieves a stop signal if intercepts
        cherrypy.engine.subscribe('stop',
            lambda: (server_thread.join(timeout=5), shutdown_event.set())
        )
        # SIGTERM is not claimed by CherryPy, so handle it directly.
        signal.signal(signal.SIGTERM, lambda signum, frame: shutdown_event.set())
        return server_thread, shutdown_event


    def _run_server(self):
        # Configure and start cherrypy engine
        cherrypy.quickstart(
            self,
            "/api/v1/",
            {
                'global': {'server.socket_host': self._server_host, 'server.socket_port': self._server_port, 'server.socket_timeout': 3},
            },
        )


    def stop(self):
        logger.info("Shutdown signal received, shutting down...")
        cherrypy.engine.exit()
        if self._server_thread is not None:
            self._server_thread.join(timeout=5)
        else:
            logger.warning("Server thread could not be found. Assumed to be joined and shutting down.")