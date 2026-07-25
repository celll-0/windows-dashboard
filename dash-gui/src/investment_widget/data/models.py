"""Domain entities. Pure data — no Qt, no I/O, no formatting."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class AccountSummary:
    current_value: float
    realized_pl: float
    total_cost: float
    unrealized_pl: float
    total_value: float
    free_cash: float
    timestamp: datetime

    @property
    def total_pl(self) -> float:
        return self.unrealized_pl + self.realized_pl

    @classmethod
    def from_dict(cls, data: dict) -> "AccountSummary":
        """Parse the endpoint payload. Values are plain numbers (no symbols)."""
        inv = data["investments"]

        return cls(
            current_value=float(inv["currentValue"]),
            realized_pl=float(inv["realizedProfitLoss"]),
            total_cost=float(inv["totalCost"]),
            unrealized_pl=float(inv["unrealizedProfitLoss"]),
            total_value=float(inv["totalValue"]),
            free_cash=float(inv["availableToTrade"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )