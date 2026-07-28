"""create a cherrypy server and run in a new thread to serve the the store.json data."""

import cherrypy
from loguru import logger

from .services import StoreLike, PersistenceService
from .constants import SERVICES_DEFAULT_PORT, SERVICES_PORT, SERVER_HOST


class DashboardDataServer(object):
    _data_client: StoreLike = PersistenceService

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


def run_server():
    """
    Subscribes single scheduler/task executor application to cherrypy engine lifecyle.
    Chosen methods are exposed at the base url on port 8080 (default).

    TODO: secure application endpoints with shared app credentials (can be managed through
    env vars). See auth_digest tool authentication
    """
    cherrypy.server.socket_host = SERVER_HOST
    cherrypy.server.socket_port = SERVICES_PORT
    if cherrypy.server.socket_port == SERVICES_DEFAULT_PORT:
        logger.warning(
            f"Dashboard Data Server is running on default port {SERVICES_DEFAULT_PORT}. This may cause conflicts with other applications. Check port in the .env file."
        )

    cherrypy.server.socket_timeout = 3
    cherrypy.engine.autoreload.unsubscribe()

    # Configure and start cherrypy engine
    dashboard_data_server = DashboardDataServer()

    cherrypy.quickstart(
        dashboard_data_server,
        "/api/v1/",
        {
            'global': {'server.socket_host': '0.0.0.0', 'server.socket_port': SERVICES_PORT, 'server.socket_timeout': 3},
        },

    )
