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
        return cls(
            current_value=float(data["currentValue"]),
            realized_pl=float(data["realizedProfitLoss"]),
            total_cost=float(data["totalCost"]),
            unrealized_pl=float(data["unrealizedProfitLoss"]),
            total_value=float(data["totalValue"]),
            free_cash=float(data["availableToTrade"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass(frozen=True)
class Position:
    ticker: str
    name: str
    current_price: float
    quantity: float
    current_value: float
    total_cost: float
    unrealized_pl: float

    @classmethod
    def from_dict(cls, ticker: str, data: dict) -> "Position":
        return cls(
            ticker=ticker,
            name=data["name"],
            current_price=float(data["currentPrice"]),
            quantity=float(data["quantity"]),
            current_value=float(data["currentValue"]),
            total_cost=float(data["totalCost"]),
            unrealized_pl=float(data["unrealizedPl"]),
        )


@dataclass(frozen=True)
class OpenPositions:
    positions: list[Position]
    timestamp: datetime

    @classmethod
    def from_dict(cls, data: dict) -> "OpenPositions":
        """Parse the endpoint payload: ticker-keyed positions plus a sibling timestamp."""
        return cls(
            positions=[
                Position.from_dict(ticker, position)
                for ticker, position in data.items()
                if ticker != "timestamp"
            ],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )