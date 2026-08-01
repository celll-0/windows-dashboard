"""Initiate the application instance and load main window"""

import sys
from pathlib import Path

from loguru import logger

from dash.server import DailyBriefServer
from dash.daily_brief_app import DailyBriefApplication

# Make shared project-root packages (e.g. utils) importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


if Path(__file__).resolve().parent.parent.joinpath(".env").exists():
    from dotenv import load_dotenv
    load_dotenv()

from dash.config import TaskConfigs
from dash.paths import LOGGING_CONFIG_PATH
from logging_conf import load_logging_config

def main():
    # Load logging configuration from file
    load_logging_config(LOGGING_CONFIG_PATH) # app/project.toml or pyproject.toml
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
