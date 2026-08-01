from typing import Dict, Any
from loguru import logger

from dash.constants import ACTIVE_TASKS
from dash.tasks import TASK_HANDLER_MAP
from dash.scheduling import (
    DataObserver,
    LoggingObserver,
    RecurringTimeSchedulingStrategy,
    RecurringSchedulingStrategy,
    OneTimeSchedulingStrategy,
)
from dash.services.schedulingService import TaskSchedulerService



_STRATEGY_BUILDERS = {
    "recurring_time": lambda s: RecurringTimeSchedulingStrategy(time=s.time),
    "interval": lambda s: RecurringSchedulingStrategy(interval=s.interval),
    "one_time": lambda s: OneTimeSchedulingStrategy(execution_time=s.execution_time),
}


class DailyBriefApplication:
    scheduler: TaskSchedulerService
    task_configs: Dict[str, Any]

    def __init__(self, task_configs: Dict[str, Any]):
        self.scheduler = TaskSchedulerService.getInstance()
        self.task_configs = task_configs

    def run(self):
        logger.info("Application started. Initializing scheduled tasks...")
        self.scheduler.initialize(worker_count=2)
        for task_name in ACTIVE_TASKS:
            task_conf = self.task_configs[task_name]
            # only set up task if it has registered schedules
            if hasattr(task_conf, "schedules") and task_conf.schedules:
                task_handler = TASK_HANDLER_MAP.get(task_conf.name)
                opts: Dict[str, Any] = {} # TODO: Define a scheduler task options type to avoid using a generic dict here
                if task_handler is None:
                    logger.warning(f"No task handler found for {task_conf.name}. Skipping scheduling.")
                    continue

                task = task_handler()
                if (
                    hasattr(task_conf, "callback") and task_conf.callback
                    and task_conf.callback in TASK_HANDLER_MAP
                ):
                    callback_handler = TASK_HANDLER_MAP.get(task_conf.callback)
                    if callback_handler is not None:
                        callback = callback_handler()
                        opts["callback"] = callback.set_caller(task) if task.is_data_task else callback  # Set the caller for the callback task
                    else:
                        logger.warning(f"No callback handler found for {task_conf.callback}.")
                else:
                    logger.warning(f"No callback registered for task {task_conf.name}.")

                for sched in task_conf.schedules:
                    opts["strategy"] = _STRATEGY_BUILDERS[sched.type](sched)
                    self.scheduler.schedule(task, **opts)
            else:
                logger.warning(f"No schedules defined for task {task_conf.name}. Please add via config.py.")

        self.scheduler.addObserver(LoggingObserver())
        # Pass persistance client as store object param
        self.scheduler.addObserver(DataObserver())


    def shutdown(self):
        self.scheduler.shutdown()

