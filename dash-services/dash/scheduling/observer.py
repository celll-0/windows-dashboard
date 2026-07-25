import threading
from abc import ABC, abstractmethod
from typing import Dict, List

from loguru import logger
from pydantic import BaseModel, PrivateAttr

from ..config import TaskConfigs
from ..services import StoreLike
from .scheduledTask import ScheduledTask


class TaskExecutionObserver(ABC, BaseModel):
    @abstractmethod
    def on_task_started(self, started: ScheduledTask) -> None:
        pass

    @abstractmethod
    def on_task_completed(self, completed: ScheduledTask) -> None:
        pass

    @abstractmethod
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
    _store: StoreLike = PrivateAttr()
    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, store: StoreLike):
        # duck typing to validate store service that then add instatiate it as store property
        if hasattr(store, 'update') and hasattr(store, 'get_from_table'):
            self._store = store
        else:
            raise TypeError("Data observer couldn't be instantiated. Must provide a valid store client")

    def on_task_started(self, started: ScheduledTask) -> None:
        # Potential add a health check on gui to ensure responsiveness of the app and that the store is available
        pass

    def on_task_completed(self, completed: ScheduledTask) -> None:
        # Route to the correct UI update callback based on the task's name
        task = completed.task
        if task.get_name() == TaskConfigs['FETCH_SUMMARY'].name:
            investment_data = task.data
            if not investment_data or investment_data is None:
                logger.warning(
                    "No investment data returned from task '{}'... Skipping store update", task.get_name()
                )
                return
            try:
                self._store.update(investment_data, 'investments')
                logger.info("Investment data updated successfully in the store")
            except Exception as e:
                logger.error("Failed updating store: {}", e)
                raise

    def on_task_failed(self, failed: ScheduledTask, exception: Exception) -> None:
        # Prompt bridge to show stale data warning if the task fails
        task_name = failed.task.get_name()
        if task_name == TaskConfigs['FETCH_SUMMARY'].name:
            logger.info(f"'{task_name}' couldn't fetch investment summary, current store state unchanged")
