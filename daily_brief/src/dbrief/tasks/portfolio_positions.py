
import re
from typing import Optional
from pydantic import PrivateAttr

from dbrief.config import TaskConfigs
from dbrief.exceptions import TaskExecutionError
from dbrief.scheduling.task import Task
from dbrief.services import (
    InvestmentDataService,
    InvestmentsService
)

task_config = TaskConfigs["FETCH_PORTFOLIO_POSITIONS"]

class FetchPortfolioPositionsTask(Task):
    investmentsService: InvestmentDataService = InvestmentsService
    _store_in: Optional[str] = PrivateAttr(default_factory=lambda: task_config.store_in)
    _name: str = PrivateAttr(default_factory=lambda: task_config.name)
    _gui_type: Optional[str] = PrivateAttr(default_factory=lambda: task_config.data_type)
    _data_task: bool = PrivateAttr(default=True)

    def get_name(self) -> str:
        return self._name

    def execute(self) -> None:
        """Get the latest portfolio positions from the investments service."""
        try:
            portfolio_positions = self.investmentsService.get_positions()
            if portfolio_positions and portfolio_positions is not None:
                if not self.store_key:
                    raise ValueError("Store key is not defined for storing portfolio positions.")

                reshaped = {}
                for position in portfolio_positions:
                    instrument = position['instrument']
                    ticker = instrument['ticker']
                    wallet = position['walletImpact']
                    # Trading212 tacks a lowercase currency/exchange suffix onto
                    # LSE tickers (e.g. "IGLNl_EQ", "SXRUd_EQ") -- strip it so the
                    # displayed name is just the up-to-4-letter ticker symbol.
                    display_name = re.sub(r'[a-z]+$', '', ticker.split('_')[0])[:4]
                    reshaped[ticker] = {
                        'ticker': ticker,
                        'name': display_name,
                        'currentPrice': position['currentPrice'],
                        'quantity': position['quantity'],
                        'totalCost': wallet['totalCost'],
                        'currentValue': wallet['currentValue'],
                        'unrealizedPl': wallet['unrealizedProfitLoss'],
                    }
                self._data[self.store_key] = reshaped

        except Exception as e:
            raise TaskExecutionError(
                "Failed to fetch portfolio positions", task_name=self.get_name()
            ) from e