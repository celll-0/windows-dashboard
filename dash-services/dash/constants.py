from os import getenv


T212_BASE_URL = getenv('TRADING212_BASE_URL')

# GUI configuration
GUI_HOST = getenv('GUI_HOST')
GUI_PORT = getenv('GUI_PORT')

# Server configuration
SERVER_HOST = getenv('SERVER_HOST')
SERVICES_DEFAULT_PORT = 8000
SERVICES_PORT = int(getenv('SERVICES_PORT', SERVICES_DEFAULT_PORT))

# Delay (s) before executing a callback task after the main task completes
CALLBACK_DELAY = 1

# Timeout (s) to wait for the widget to be ready before pushing data
WIDGET_READY_TIMEOUT = 20

TIMEZONE = 'Europe/London' 

ACTIVE_TASKS = (
    "FETCH_SUMMARY",
    "FETCH_PORTFOLIO_POSITIONS",
)

STORE_TABLES = [
    "investments",
    "news"
]