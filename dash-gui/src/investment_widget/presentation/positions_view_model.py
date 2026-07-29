"""Maps a list of domain ``Position``s into the top-3-movers view model the
QML movers section binds to. Keys are camelCase, mirroring ``view_model.py``.
"""
from __future__ import annotations

from ..data import Position
from .formatting import arrow, money, sign_color


def _pl_ratio(position: Position) -> float:
    if not position.total_cost:
        return 0.0
    return position.unrealized_pl / position.total_cost


def build_positions_view_model(positions: list[Position]) -> list[dict]:
    """Rank positions by unrealized P/L % magnitude and return the top 3."""
    top = sorted(positions, key=lambda p: abs(_pl_ratio(p)), reverse=True)[:3]

    return [
        {
            "ticker": position.ticker,
            "name": position.name,
            "currentValue": money(position.current_value),
            "price": money(position.current_price),
            "pl": money(abs(position.unrealized_pl)),
            "plColor": sign_color(position.unrealized_pl),
            "plArrow": arrow(position.unrealized_pl),
        }
        for position in top
    ]
