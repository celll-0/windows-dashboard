from datetime import datetime, time, timedelta
from .constants import GUI_HOST, GUI_PORT, _



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
    "FETCH_NEWS_FEED": _(
        name="fetch_news_feed",
        schedules=[],
        callback="push_to_widget",
        store_in="news.feed",
        data_type="NewsFeed"
    ),
    "LOGIN_TO_GN": _(
            name="login_to_ground_news",
        schedules=[],
        callback="push_to_widget",
        store_in="news.auth",
        data_type="NewsCredentials"
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
    "GUI": _(
        base_url=f"http://{GUI_HOST}:{GUI_PORT}",
        endpoints=_(
            widget_ingest="/ingest/update"
        )
    ),
    "FIREBASE_ID": _(
        base_url="https://identitytoolkit.googleapis.com/v1",
        endpoints=_(
            sign_in="/accounts:signInWithPassword",
            user_lookup="/accounts:lookup",
            refresh_token="/v1/token"
        )
    ),
    "GN": _(
        base_url="https://web-api-cdn.ground.news",
        endpoints=_(
            subscribed_topics="/api/v04/interests/listMy",
            interest_feed="/api/v06/story/feed/interest/:id/ids",
            interest_top_stories="/api/public/interest/:id/events/top",
            story="/api/v06/story/:id/web",
            login="/api/v04/user/login"
        )
    ),
}