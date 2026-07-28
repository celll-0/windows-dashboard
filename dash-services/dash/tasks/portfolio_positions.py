
from typing import Optional
from pydantic import PrivateAttr

from dash.config import TaskConfigs
from dash.scheduling.task import Task
from dash.services.investmentsService import (
    InvestmentDataService,
    InvestmentsService
)

task_config = TaskConfigs["FETCH_PORTFOLIO_POSITIONS"]

class FetchPortfolioPositionsTask(Task):
    investmentsService: InvestmentDataService = InvestmentsService
    _store_in: Optional[str] = PrivateAttr(default_factory=lambda: task_config.store_in)
    _name: str = PrivateAttr(default_factory=lambda: task_config.name)
    _data_task: bool = PrivateAttr(default=True)

    def get_name(self) -> str:
        return self._name

    def execute(self) -> None:
        """Get the latest portfolio positions from the investments service."""
        try:
            portfolio_positions = self.investmentsService.get_positions()
            if portfolio_positions and portfolio_positions is not None:
                # Extract the nested investments object; default to empty dict if missing
                if not self.store_key:
                    raise ValueError("Store key is not defined for storing portfolio positions.")
                self._data = {
                    self.store_key: {
                        position['instrument']['ticker']: position
                        for position in portfolio_positions
                    }
                }

        except Exception as e:
            raise e