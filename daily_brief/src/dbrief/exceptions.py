from typing import Any, Dict, Optional


class DashError(Exception):
    """Base class for all custom dash-services exceptions.

    Carries structured `context` so observers/loggers can bind it to log
    records instead of stuffing everything into the message string.
    """

    def __init__(self, message: str, *, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}


class TaskExecutionError(DashError):
    """Raised when a scheduled task fails inside execute().

    Preserves the task name so the scheduler and observers can log which
    task failed without losing the original exception (chain with
    `raise TaskExecutionError(...) from e`).
    """

    def __init__(
        self,
        message: str,
        *,
        task_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, context=context)
        self.task_name = task_name


class TaskStatePersistenceRequired(TaskExecutionError):
    """Flag exception: the task failed but had already accumulated partial
    `_data` that must not be discarded.

    The scheduler's `DataObserver` checks
    `isinstance(exception, TaskStatePersistenceRequired)` in
    `on_task_failed` and, when `partial_data` is present, flushes it to
    `store_table_name`/`store_key` instead of dropping it.
    """

    def __init__(
        self,
        message: str,
        *,
        task_name: Optional[str] = None,
        partial_data: Optional[Dict[str, Any]] = None,
        store_table_name: Optional[str] = None,
        store_key: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, task_name=task_name, context=context)
        self.partial_data = partial_data or {}
        self.store_table_name = store_table_name
        self.store_key = store_key
