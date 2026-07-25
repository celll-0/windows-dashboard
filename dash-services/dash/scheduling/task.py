from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from pydantic import BaseModel, PrivateAttr

from ..config import TaskConfigs
from ..services.investmentsService import InvestmentsService
from ..services.persistenceClient import JsonPersistenceClient


class Task(ABC, BaseModel):
    _data: Optional[Dict[str, Any]] = PrivateAttr(default={})

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


class FetchSummaryTask(Task):
    investmentsService: InvestmentsService
    _name: str = PrivateAttr(default_factory=lambda: TaskConfigs["FETCH_SUMMARY"].name)

    def get_name(self) -> str:
        return self._name

    def execute(self) -> None:
        """Get the latest summary data from the investments service."""
        try:
            summary_data = self.investmentsService.get_summary()
            if summary_data and summary_data is not None:
                # Extract the nested investments object; default to empty dict if missing
                self._data = {
                    **summary_data.get("investments", {}),
                    **summary_data.get("cash", {}),
                    "totalValue": summary_data.get("totalValue"),
                }

        except Exception as e:
            raise e
    
class UpdateGuiSummaryTask(Task):
    store: JsonPersistenceClient
    investmentsService: InvestmentsService
    _name: str = PrivateAttr(default_factory=lambda: TaskConfigs["UPDATE_GUI_SUMMARY"].name)

    def get_name(self) -> str:
        return self._name

    def execute(self) -> None:
        """Get the latest summary data from the store and push it to the widget."""
        ts, investment_data = self.store.get_from_table('investments')
        # Construct a summary dict to send to the widget.
        summary = {
            "timestamp": ts,
            "investments": investment_data
        }
        # only push to the GUI if all values are present and not None
        if all(summary.values()):
            success = self.investmentsService.push_summary_to_gui(summary)
            if success:
                logger.success("Gui summary updated to latest!")
            else:
                raise RuntimeError("Failed to push summary to gui.")

