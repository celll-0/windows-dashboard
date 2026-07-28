import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, PrivateAttr

from .task import Task
from .schedulingStrategy import SchedulingStrategy
from .taskStatus import TaskStatus


class ScheduledTask(BaseModel):
    # Public constructor fields
    task: Task
    strategy: SchedulingStrategy
    sequence_number: int
    callback: Optional[Task] = None  # Optional callback task to execute after this task completes

    # Private per-instance state
    _id: str = PrivateAttr(default_factory=lambda: str(uuid.uuid4()))
    _last_execution_time: Optional[datetime] = PrivateAttr(default=None)
    _status: TaskStatus = PrivateAttr(default=TaskStatus.SCHEDULED)
    _next_execution_time: Optional[datetime] = PrivateAttr(default=None)

    def model_post_init(self, __context) -> None:
        # Ask the strategy for the initial execution time.
        # Passing None signals "this task has never run before."
        self._next_execution_time = self.strategy.get_next_execution_time(None)

    @property
    def id(self) -> str:
        return self._id

    @property
    def next_execution_time(self) -> datetime:
        if self._next_execution_time is None:
            raise ValueError("Next execution time is not defined for this task.")
        return self._next_execution_time 

    @property
    def status(self) -> TaskStatus:
        return self._status
    
    @property
    def callback_task(self) -> Optional[Task]:
        return self.callback

    @status.setter
    def status(self, value: TaskStatus) -> None:
        self._status = value

    def has_more_executions(self):
        return self.strategy.get_next_execution_time(self._last_execution_time) is not None

    # Called after execution completes. Records the actual finish time
    # then asks the strategy for the next run.
    def update_for_next_execution(self):
        self._last_execution_time = datetime.now()
        next_time = self.strategy.get_next_execution_time(self._last_execution_time)
        self._next_execution_time = next_time

    def __lt__(self, other: 'ScheduledTask') -> bool:
        # None execution times get pushed to the back of the queue
        if self._next_execution_time is None and other._next_execution_time is None:
            return False
        if self._next_execution_time is None:
            return False
        if other._next_execution_time is None:
            return True

        # Primary sort: earliest execution time first (min-heap)
        if self._next_execution_time != other._next_execution_time:
            return self._next_execution_time < other._next_execution_time

        # Tiebreaker: lower sequence number first (FIFO for same-time tasks)
        return self.sequence_number < other.sequence_number

    def __gt__(self, other: 'ScheduledTask') -> bool:
        return not self.__lt__(other) and self != other

    def __repr__(self) -> str:
        return f"ScheduledTask[{self.task.get_name()}, next={self._next_execution_time}, status={self._status}]"
