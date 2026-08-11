"""Initiate the application instance and load main window"""

import sys
from pathlib import Path

from loguru import logger

from dbrief.server import DailyBriefServer
from dbrief.daily_brief_app import DailyBriefApplication
from dbrief.services.database import PersistenceService

# Make shared project-root packages (e.g. utils) importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dbrief.config import TaskConfigs
from dbrief.paths import LOGGING_CONFIG_PATH
from logging_conf import load_logging_config



def main():
    load_logging_config(LOGGING_CONFIG_PATH) # app/project.toml or pyproject.toml

    PersistenceService.initialize_store()
    
    app = DailyBriefApplication(TaskConfigs)
    app.run()

    server = DailyBriefServer()
    server_thread, shutdown_event = server.init_server_thread()

    try:
        server_thread.start()
        shutdown_event.wait()
    except KeyboardInterrupt:
        server.stop()
    except Exception as e:
        logger.exception("There was an issue while starting the server", e)
    finally:
        app.shutdown()
        if server_thread.is_alive():
            logger.info("Server thread lingered after shutdown. Joining...")
            server_thread.join(timeout=5)



if __name__ == "__main__":
    main()
