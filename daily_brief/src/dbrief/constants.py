from os import getenv
from types import SimpleNamespace

T212_BASE_URL = getenv('TRADING212_BASE_URL')

# GUI configuration
GUI_HOST = getenv('GUI_HOST')
DEFAULT_GUI_PORT = getenv('DEFAULT_GUI_PORT', 8001)
GUI_PORT = getenv('GUI_PORT', DEFAULT_GUI_PORT)

# Server configuration
SERVER_HOST = '0.0.0.0'
SERVICES_DEFAULT_PORT = getenv('DEFAULT_SERVICES_PORT', 8002)
SERVICES_PORT = int(getenv('SERVICES_PORT', SERVICES_DEFAULT_PORT))

# Delay (s) before executing a callback task after the main task completes
CALLBACK_DELAY = 1

# Timeout (s) to wait for the widget to be ready before pushing data
WIDGET_READY_TIMEOUT: float = 20

# News service
INTEREST_STORY_FETCH_LIMIT = 6

TIMEZONE = 'Europe/London' 

ACTIVE_TASKS = (
    "FETCH_SUMMARY",
    "FETCH_PORTFOLIO_POSITIONS",
    "FETCH_NEWS_FEED"
)

STORE_TABLES = [
    "investments",
    "news"
]

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
