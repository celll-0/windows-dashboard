from os import getenv
from types import SimpleNamespace

class _(SimpleNamespace):
    """Read-only SimpleNamespace. Prevents accidental mutation of constant
    values and allows dot-notation access. Raises AttributeError on mutation.
    """
    def __setattr__(self, name, value):
        raise AttributeError("Namespace is read-only")

    def __delattr__(self, name):
        raise AttributeError("Namespace is read-only")


SNAPSHOT_RETENTION_HOURS = 24

# Single source of truth for provider endpoint paths, appended to
# Config.base_url by ApiClient. Grouped under "investments" to mirror the
# provider's own store_in="investments.summary"/"investments.positions"
# namespacing (dash-services/dash/config.py).
_PROVIDER_ENDPOINTS = _(
    investments=_(
        summary="/summary",
        positions="/positions",
    ),
    news=_(
        feed="/news_feed",
    ),
)

DEFAULT_PORT = getenv("DEFAULT_GUI_PORT", 8001)
DEFAULT_SERVICES_PORT = getenv("DEFAULT_SERVICES_PORT", 8002)

DESCRIPTION_LIMIT = 140

# Single duration for every QML transition/behaviour (hover tints, collapse
# animations, etc.) -- exposed to QML as a root-context property (see
# app.py) so all UI motion stays smooth and consistent, not just individual
# components that happen to import the same value.
ANIMATION_DURATION_MS = 120
