from typing import Protocol
from typing import Any, Dict
from dbrief.services.investments import (
    InvestmentsService, InvestmentDataService
)
from dbrief.services.database import PersistenceService
from dbrief.services.news import NewsService, GroundNewsService


class StoreLike(Protocol):
    def update(self, data: Dict[str, Any], table_name: str) -> None: ...
    def get_from_table(self, table_name: str) -> Dict[str, Any]: ...


__all__ = [
    "InvestmentsService",
    "PersistenceService",
    "StoreLike",
    "InvestmentDataService",
    "NewsService",
    "GroundNewsService",
]
