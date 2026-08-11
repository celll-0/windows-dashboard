"""Pure presentation helpers: money formatting, sign-based colours and arrows.

These encode the design's colour convention (#3B6D11 positive, #A32D2D
negative) in one place so the view model and QML stay consistent.
"""
from __future__ import annotations

POS_GREEN = "#8FCF5D"
NEG_RED = "#E17C7C"
GREY = "#A8AAA2"
MUTED = "#9FA197"


def money(value: float) -> str:
    return f"£ {value:,.2f}"


def arrow(value: float) -> str:
    return "↗" if value >= 0 else "↙"


def sign_color(value: float) -> str:
    return POS_GREEN if value >= 0 else NEG_RED
