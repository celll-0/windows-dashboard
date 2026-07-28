import heapq
import threading
from datetime import datetime, timedelta
from typing import List, Optional

from loguru import logger
from ..constants import CALLBACK_DELAY

from ..scheduling.observer import TaskExecutionObserver
from ..scheduling.scheduledTask import ScheduledTask
from ..scheduling.schedulingStrategy import SchedulingStrategy, OneTimeSchedulingStrategy
from ..scheduling.task import Task
from ..scheduling.taskStatus import TaskStatus


class TaskSchedulerService:
    # Class-level lock for singleton initialization
    _instance: Optional['TaskSchedulerService'] = None
    _instance_lock = threading.Lock()

    _task_queue: list = []  # Min-heap via heapq, ordered by execution time
    _condition = threading.Condition()  # Combines lock + wait/notify coordination
    _observers: List[TaskExecutionObserver] = []
    _observers_lock = threading.Lock()  # Protects the observers list
    _workers: List[threading.Thread] = []
    _running: bool = False
    _sequence_counter: int = 0

    @classmethod
    def getInstance(cls) -> 'TaskSchedulerService':
        # check whether the an instance already exists
        if cls._instance is None:
            # Obtain the lock and perform second check in case an instance was created in this time
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = TaskSchedulerService()
        # Always return the singleton instance
        return cls._instance

    def initialize(self, worker_count: int):
        if worker_count <= 0:
            raise ValueError("Worker count must a positive integer")

        self._running = True
        for i in range(worker_count):
            worker: threading.Thread = threading.Thread(
                target=self._run_worker, name=f'Scheduler_worker_{i}', daemon=True
            )
            self._workers.append(worker)
            worker.start()
        logger.info(f"Started {worker_count} scheduler worker threads!")

    def schedule(self, task: Task, strategy: SchedulingStrategy, callback: Optional[Task] = None) -> str:
        if not self._running:
            raise RuntimeError("Scheduler is not running!")

        with self._condition:
            # Increment to sequence counter task can be sorted pass execution_time
            self._sequence_counter = self._sequence_counter + 1
            scheduled_task: ScheduledTask = ScheduledTask(
                task=task,
                strategy=strategy,
                sequence_number=self._sequence_counter,
                callback=callback
            )
            heapq.heappush(self._task_queue, scheduled_task)

            logger.info(
                "Task '{}' scheduled for {}",
                task.get_name(),
                scheduled_task.next_execution_time.strftime("%d %b %Y at %H:%M:%S"),
                scheduled_task.callback.get_name() if scheduled_task.callback else "None",
            )

            if scheduled_task.callback:
                logger.info(
                    "Callback task '{}' scheduled to run on completion of '{}'",
                    scheduled_task.callback.get_name(),
                    task.get_name(),
                )

            self._condition.notify_all()
        return scheduled_task.id

    def cancel(self, task_id: str) -> bool:
        with self._condition:
            for i, task in enumerate(self._task_queue):
                if task.id == task_id:
                    task.status = TaskStatus.CANCELLED
                    self._task_queue.pop(i)
                    heapq.heapify(self._task_queue)
                    return True
            logger.warning(f"Could not cancel task [{task_id}. It has either already executed or given id is invalid]")
            # Task not found - executed or invalid id
            return False

    def addObserver(self, observer: TaskExecutionObserver) -> None:
        with self._observers_lock:
            self._observers.append(observer)

    def shutdown(self):
        with self._condition:
            self._running = False
            # Notify any worker sleeping in wait()
            self._condition.notify_all()
        for worker in self._workers:
            worker.join()
        logger.info("Scheduler shutting down")

    def _run_worker(self) -> None:
        while self._running:
            task: Optional[ScheduledTask] = None

            with self._condition:
                while self._running:
                    # If the queue is empty, wait until it's not
                    if not self._task_queue:
                        # Wait until schedule or shutdowm method calls notify_all
                        self._condition.wait()
                        continue

                    # If it's not empty grab the next task
                    # determine how long until the tasks execute_time
                    next_task: ScheduledTask = self._task_queue[0]
                    now: datetime = datetime.now()
                    delay: float = (next_task.next_execution_time - now).total_seconds()

                    # pop the task from queue if it's time to execute or wait out the delay.
                    if delay <= 0:
                        task = heapq.heappop(self._task_queue)
                        break
                    else:
                        self._condition.wait(delay)

            if task is not None and task.status != TaskStatus.CANCELLED:
                self._execute_task(task)

    def _execute_task(self, scheduled_task: ScheduledTask) -> None:
        scheduled_task.status = TaskStatus.RUNNING
        self._notify_observers(scheduled_task, "started")

        try:
            scheduled_task.task.execute()
            scheduled_task.status = TaskStatus.COMPLETED
            self._notify_observers(scheduled_task, "completed")
        except Exception as e:
            # Catch ALL exceptions so a failing task never kills the worker
            scheduled_task.status = TaskStatus.FAILED
            self._notify_observers_failed(scheduled_task, e)

        if (
            scheduled_task.callback_task is not None and 
            scheduled_task.status == TaskStatus.COMPLETED
        ):
            # Schedule the callback task to run immediately after the main task completes
            self.schedule(
                task=scheduled_task.callback_task,
                strategy=OneTimeSchedulingStrategy(execution_time=(datetime.now() + timedelta(seconds=CALLBACK_DELAY))),
            )

        # Whether the task succeeded or failed, check if it should run again.
        # For one-time tasks, update_for_next_execution() sets next_execution_time to None.
        # For recurring tasks, it calculates the next run time.
        scheduled_task.update_for_next_execution()
        if scheduled_task.next_execution_time is not None:
            scheduled_task.status = TaskStatus.SCHEDULED
            with self._condition:
                heapq.heappush(self._task_queue, scheduled_task)
                logger.info(
                    "Task '{}' rescheduled for {}",
                    scheduled_task.task.get_name(),
                    scheduled_task.next_execution_time.strftime("%d %b %Y at %H:%M:%S"),
                )
                # Wake workers so they re-evaluate the new queue head
                self._condition.notify_all()

    def _notify_observers(self, task: ScheduledTask, event: str) -> None:
        with self._observers_lock:
            observers_snapshot = list(self._observers)
        for observer in observers_snapshot:
            try:
                if event == "started":
                    observer.on_task_started(task)
                elif event == "completed":
                    observer.on_task_completed(task)
            except Exception as e:
                logger.warning("An issue occurred while notifying observers")
                logger.exception(e)
                # Observer failures must NEVER affect task execution or scheduling.
                # A broken logger should not prevent tasks from running.
                pass

    def _notify_observers_failed(self, task: ScheduledTask, exception: Exception) -> None:
        with self._observers_lock:
            observers_snapshot: List[TaskExecutionObserver] = list(self._observers)
        for observer in observers_snapshot:
            try:
                observer.on_task_failed(task, exception)
            except Exception as e:
                logger.error("An issue occurred while notifying observers")
                logger.exception(e)
                # Observer errors are silently swallowed
                pass

    # For testing: allows resetting the singleton between test cases
    @classmethod
    def reset_instance(cls) -> None:
        with cls._instance_lock:
            cls._instance = None
