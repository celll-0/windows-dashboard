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
)