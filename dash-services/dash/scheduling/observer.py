import threading
from abc import ABC, abstractmethod
from zoneinfo import ZoneInfo
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from ..constants import TIMEZONE
from ..services import StoreLike, PersistenceService
from .scheduledTask import ScheduledTask


class TaskExecutionObserver(ABC, BaseModel):
    def on_task_started(self, started: ScheduledTask) -> None:
        pass

    @abstractmethod
    def on_task_completed(self, completed: ScheduledTask) -> None:
        pass

    def on_task_failed(self, failed: ScheduledTask, exception: Exception) -> None:
        pass


class LoggingObserver(TaskExecutionObserver):
    def on_task_started(self, started: ScheduledTask) -> None:
        thread_name = threading.current_thread().name
        logger.info("[{}] Task '{}' started", thread_name, started.task.get_name())

    def on_task_completed(self, completed: ScheduledTask) -> None:
        thread_name = threading.current_thread().name
        logger.success("[{}] Task '{}' completed successfully", thread_name, completed.task.get_name())

    def on_task_failed(self, failed: ScheduledTask, exception: Exception) -> None:
        thread_name = threading.current_thread().name
        logger.error("[{}] Task '{}' failed", thread_name, failed.task.get_name())
        logger.exception(exception)


class DataObserver(TaskExecutionObserver):
    # TODO: create store Object with method to persist result (like 'self.store.update({investment_fields: <some date>})')
    _store: StoreLike = PersistenceService
    model_config = {"arbitrary_types_allowed": True}


    def on_task_started(self, started: ScheduledTask) -> None:
        # Potential add a health check on gui to ensure responsiveness of the app and that the store is available
        pass

    def on_task_completed(self, completed: ScheduledTask) -> None:
        """
        Update the store for data tasks that have data to persist with the timestamp. If the 
        task is not a data task or has no data, skip the store update. 
        """
        task = completed.task
        if task.is_data_task and task._data:
            investment_data = task.data or {}
            try:
                # require data tasks to define a valid store table name/key for
                # persistence, otherwise raise an exception
                if not task.store_table_name:
                    raise ValueError("Task does not name a valid table for data persistence")
                if not task.store_key or task.store_key not in investment_data:
                    raise ValueError("Task does not name a valid store key for data persistence")
                investment_data[task.store_key]["timestamp"] = datetime.now(tz=ZoneInfo(TIMEZONE)).isoformat()
                self._store.update(investment_data, task.store_table_name)
                logger.info("Investment data updated successfully in the store")
            except Exception as e:
                logger.error("Failed updating store: {}", e)
                raise
        elif task.is_data_task:
            logger.warning(
                "No investment data returned from task '{}'... Skipping store update", task.get_name()
            )
            return