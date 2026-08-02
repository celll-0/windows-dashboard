
from typing import Optional
from pydantic import PrivateAttr

from dash.config import TaskConfigs
from dash.scheduling.task import Task
from dash.services.investments import (
    InvestmentsService,
    InvestmentDataService
)

task_config = TaskConfigs["FETCH_SUMMARY"]

class FetchSummaryTask(Task):
    investmentsService: InvestmentDataService = InvestmentsService
    _name: str = PrivateAttr(default_factory=lambda: task_config.name)
    _store_in: Optional[str] = PrivateAttr(default_factory=lambda: task_config.store_in)
    _gui_type: Optional[str] = PrivateAttr(default_factory=lambda: task_config.data_type)
    _data_task: bool = PrivateAttr(default=True)


    def get_name(self) -> str:
        return self._name

    def execute(self) -> None:
        """Get the latest summary data from the investments service."""
        try:
            summary_data = self.investmentsService.get_summary()
            if summary_data and summary_data is not None:
                # Extract the nested investments object; default to empty dict if missing
                if not self.store_key:
                    raise ValueError("Store key is not defined for storing portfolio positions.")
                self._data = {
                    self.store_key: {
                        **summary_data.get("investments", {}),
                        **summary_data.get("cash", {}),
                        "totalValue": summary_data.get("totalValue"),
                    }
                }

        except Exception as e:
            raise e
    