"""Maps a domain ``AccountSummary`` (+ 24h baseline) into a flat dict the QML
view binds to. Keys are camelCase because that is how they read on the QML side
(``bridge.model.totalValue``).
"""
from __future__ import annotations

from ..data import AccountSummary
from .formatting import GREY, MUTED, NEG_RED, arrow, money, sign_color

_PLACEHOLDER = "—"


def empty_view_model() -> dict:
    """All keys present with placeholders, so QML bindings never read undefined."""
    return {
        "totalValue": _PLACEHOLDER,
        "last24h": _PLACEHOLDER,
        "last24hColor": GREY,
        "ror": _PLACEHOLDER,
        "rorColor": GREY,
        "totalPl": _PLACEHOLDER,
        "totalPlColor": GREY,
        "totalPlArrow": "",
        "unrealizedPl": _PLACEHOLDER,
        "unrealizedColor": GREY,
        "realizedPl": _PLACEHOLDER,
        "realizedColor": GREY,
        "currentValue": _PLACEHOLDER,
        "totalCost": _PLACEHOLDER,
        "freeCash": _PLACEHOLDER,
        "updatedText": "",
        "updatedColor": MUTED,
    }


def build_view_model(summary: AccountSummary, baseline_value: float | None) -> dict:
    """Build the view model from a fresh summary and the ~24h-ago total value."""
    vm = empty_view_model()

    vm["totalValue"] = money(summary.total_value)

    total_pl = summary.total_pl
    vm["totalPl"] = money(total_pl)
    vm["totalPlColor"] = sign_color(total_pl)
    vm["totalPlArrow"] = arrow(total_pl)

    vm["unrealizedPl"] = money(summary.unrealized_pl)
    vm["unrealizedColor"] = sign_color(summary.unrealized_pl)
    vm["realizedPl"] = money(summary.realized_pl)
    vm["realizedColor"] = sign_color(summary.realized_pl)

    vm["currentValue"] = money(summary.current_value)
    vm["totalCost"] = money(summary.total_cost)
    vm["freeCash"] = money(summary.free_cash)

    if baseline_value:
        delta = summary.total_value - baseline_value
        ror = delta / baseline_value * 100
        vm["last24h"] = f"{arrow(delta)} {money(abs(delta))}"
        vm["last24hColor"] = sign_color(delta)
        vm["ror"] = f"{arrow(ror)} {abs(ror):.1f}%"
        vm["rorColor"] = sign_color(ror)

    local_time = summary.timestamp.astimezone().strftime("%H:%M")
    vm["updatedText"] = f"Updated {local_time}"
    return vm


def error_patch(model: dict, message: str) -> dict:
    """Return a copy of the current model with the timestamp line showing an error.

    Keeps the last known values on screen rather than blanking them.
    """
    patched = dict(model)
    patched["updatedText"] = f"Error — {message[:60]}"
    patched["updatedColor"] = NEG_RED
    return patched
