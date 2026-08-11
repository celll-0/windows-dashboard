from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, PrivateAttr


class Task(ABC, BaseModel):
    _caller: Optional["Task"] = PrivateAttr(default=None)
    _data: Dict[str, Any] = PrivateAttr(default={})
    _data_task: bool = PrivateAttr(default=False)
    _store_in: Optional[str] = PrivateAttr(default=None)
    _gui_type: Optional[str] = PrivateAttr(default=None)

    model_config = {"arbitrary_types_allowed": True}

    @abstractmethod
    def get_name(self) -> str:
        """Return human readable name of the task"""
        pass

    @abstractmethod
    def execute(self) -> None:
        """Execute the prescribed function of the task"""
        pass

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        """Return the data produced by the task after execution."""
        return self._data

    @property
    def is_data_task(self) -> bool:
        """Indicates whether the task produces data to be stored."""
        return self._data_task

    @property
    def store_table_name(self) -> Optional[str]:
        """Return the name of the store table where the data will be stored."""
        return self._store_in.split(".")[0] if self._store_in else None

    @property
    def store_key(self) -> Optional[str]:
        """Return the key under which the data will be stored in the store table."""
        return self._store_in.split(".")[-1] if self._store_in else None

    @property
    def gui_type(self) -> Optional[str]:
        """Return the GUI data type this task's output should be tagged as when pushed to the widget."""
        return self._gui_type

    @property
    def caller(self) -> Optional["Task"]:
        """Return the caller task that triggered this task, if any."""
        return self._caller
    
    def set_caller(self, caller: "Task") -> "Task":
        """Set the caller task for this task."""
        self._caller = caller
        return self