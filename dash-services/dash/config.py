from types import SimpleNamespace
from datetime import datetime, time, timedelta

from .constants import GUI_HOST, GUI_PORT


class _(SimpleNamespace):
    """
    Read-only SimpleNamespace. Prevents accidental mutation of config values.
    Also allows for dot notation access to config values.
    Raises AttributeError on mutation.
    """

    def __setattr__(self, name, value):
        raise AttributeError("Config namespace is read-only")

    def __delattr__(self, name):
        raise AttributeError("Config namespace is read-only")


# _____________________ TASK CONFIGURATIONS _____________________
TaskConfigs = {
    "FETCH_SUMMARY": _(
        name="fetch_investment_summary",
        schedules=[
            # Fetch summary on application start _____________
            _(
                type="one_time",
                execution_time=datetime.now() + timedelta(seconds=1)
            ),

            # Recurring schedules ____________________________

            _( # Just before LDN market open
                type="recurring_time",
                time=time(hour=7, minute=30, second=0)
            ),
            _( # Just after LDN market open
                type="recurring_time",
                time=time(hour=8, minute=30, second=0)
            ),
            _( # LDN market close
                type="recurring_time",
                time=time(hour=16, minute=30, second=0)
            ),
            _( # NY market open
                type="recurring_time",
                time=time(hour=14, minute=0, second=0)
            ),
            _( # NY market close
                type="recurring_time",
                time=time(hour=21, minute=30, second=0)
            ),
        ],
        callback="push_to_widget",
        store_in="investments.summary",
        data_type="AccountSummary"
    ),
    "FETCH_PORTFOLIO_POSITIONS": _(
        name="fetch_portfolio_positions",
        schedules=[
            # Fetch summary on application start _____________
            _(
                type="one_time",
                execution_time=datetime.now() + timedelta(seconds=1)
            ),
            # Recurring schedules ____________________________
            _( # Just after LDN market open
                type="recurring_time",
                time=time(hour=8, minute=30, second=0)
            ),
            _( # LDN market close
                type="recurring_time",
                time=time(hour=16, minute=30, second=0)
            ),
            _( # NY market close
                type="recurring_time",
                time=time(hour=21, minute=30, second=0)
            ),
        ],
        callback="push_to_widget",
        store_in="investments.positions",
        data_type="OpenPositions"
    ),
    "PUSH_TO_WIDGET": _(
        name="push_to_widget",
        schedules=[],
        callback=None,
    ),
}

# _______________ URL & ENDPOINT CONFIGURATIONS ________________
URLs = {
    "T212": _(
        base_url="https://live.trading212.com/api/v0",
        endpoints=_(
            summary="/equity/account/summary",
            positions="/equity/positions",
        )
    ),
    "DASH_GUI": _(
        base_url=f"http://{GUI_HOST}:{GUI_PORT}",
        endpoints=_(
            widget_ingest="/ingest/update"
        )
    ),
}