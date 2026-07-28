"""Initiate the application instance and load main window"""

import signal
import sys
import threading
from pathlib import Path
from typing import Any, Dict

# Make shared project-root packages (e.g. utils) importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cherrypy
from loguru import logger

if Path(__file__).resolve().parent.parent.joinpath(".env").exists():
    from dotenv import load_dotenv
    load_dotenv()

from dash.config import TaskConfigs
from dash.paths import LOGGING_CONFIG_PATH
from dash.constants import ACTIVE_TASKS
from dash.scheduling import (
    Task,
    DataObserver,
    LoggingObserver,
    OneTimeSchedulingStrategy,
    RecurringSchedulingStrategy,
    RecurringTimeSchedulingStrategy,
)
from dash.tasks import (
    FetchSummaryTask,
    PushToWidgetTask,
    FetchPortfolioPositionsTask,
)
from dash.server import run_server
from dash.services.schedulingService import TaskSchedulerService

from logging_conf import load_logging_config

_STRATEGY_BUILDERS = {
    "recurring_time": lambda s: RecurringTimeSchedulingStrategy(time=s.time),
    "interval": lambda s: RecurringSchedulingStrategy(interval=s.interval),
    "one_time": lambda s: OneTimeSchedulingStrategy(execution_time=s.execution_time),
}

_TASK_HANDLER_MAP: dict[str, type[Task]] = {
    "fetch_investment_summary": FetchSummaryTask,
    "push_to_widget": PushToWidgetTask,
    "fetch_portfolio_positions": FetchPortfolioPositionsTask,
}

def main():
    # Load logging configuration from file
    load_logging_config(LOGGING_CONFIG_PATH) # app/project.toml or pyproject.toml
    logger.info("Starting application")

    scheduler: TaskSchedulerService = TaskSchedulerService.getInstance()
    scheduler.initialize(worker_count=2)

    for task_name in ACTIVE_TASKS:
        task_config = TaskConfigs[task_name]
        # only set up task if it has registered schedules
        if task_config.schedules:
            task_handler = _TASK_HANDLER_MAP.get(task_config.name)
            opts: Dict[str, Any] = {}
            if task_handler is None:
                logger.warning(f"No task handler found for {task_config.name}. Skipping scheduling.")
                continue

            task = task_handler()
            if task_config.callback and task_config.callback in _TASK_HANDLER_MAP:
                callback_handler = _TASK_HANDLER_MAP.get(task_config.callback)
                if callback_handler is not None:
                    callback = callback_handler()
                    opts["callback"] = callback.set_caller(task) if task.is_data_task else callback  # Set the caller for the callback task
                else:
                    logger.warning(f"No callback handler found for {task_config.callback}.")
            else:
                logger.warning(f"No callback registered for task {task_config.name}.")

            for sched in task_config.schedules:
                opts["strategy"] = _STRATEGY_BUILDERS[sched.type](sched)
                scheduler.schedule(task, **opts)
        else:
            logger.warning(f"No schedules defined for task {task_config.name}. Please add via config.py.")

    scheduler.addObserver(LoggingObserver())
    # Pass persistance client as store object param
    scheduler.addObserver(DataObserver())

    shutdown_event = threading.Event()

    # Hook into CherryPy's own stop event so Ctrl+C (which CherryPy intercepts)
    # still triggers a clean application shutdown.
    cherrypy.engine.subscribe('stop', lambda: (server_thread.join(timeout=5), shutdown_event.set()))

    # SIGTERM is not claimed by CherryPy, so handle it directly.
    def _handle_sigterm(signum, frame):
        logger.info("Received signal {}, shutting down...", signum)
        cherrypy.engine.exit()

    signal.signal(signal.SIGTERM, _handle_sigterm)

    server_thread = threading.Thread(
        target=run_server,
        daemon=True, 
        name="main-server-thread",
    )
    server_thread.start()

    try:
        shutdown_event.wait()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received, shutting down...")
        cherrypy.engine.exit()
    finally:
        server_thread.join(timeout=5)
        scheduler.shutdown()
        logger.info("Application stopped")


if __name__ == "__main__":
    main()
