from typing import Protocol
from typing import Any, Dict
from dash.services.investmentsService import InvestmentsService
from dash.services.persistenceClient import PersistenceService


class StoreLike(Protocol):
    def update(self, data: Dict[str, Any], table_name: str) -> None: ...
    def get_from_table(self, table_name: str) -> Dict[str, Any]: ...


__all__ = ["InvestmentsService", "PersistenceService", "StoreLike"]
