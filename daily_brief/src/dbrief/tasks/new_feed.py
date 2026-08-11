from typing import Optional
from loguru import logger
from pydantic import PrivateAttr

from dbrief.config import TaskConfigs
from dbrief.services import (
    NewsService,
    GroundNewsService,
)
from dbrief.scheduling.task import Task



task_config = TaskConfigs["FETCH_NEWS_FEED"]


class FetchNewsFeedTask(Task):
    newsService: GroundNewsService = NewsService
    _name: str = PrivateAttr(default_factory=lambda: task_config.name)
    _store_in: Optional[str] = PrivateAttr(default_factory=lambda: task_config.store_in)
    _gui_type: Optional[str] = PrivateAttr(default_factory=lambda: task_config.data_type)
    _data_task: bool = PrivateAttr(default=True)


    def get_name(self) -> str:
        return self._name

    def execute(self) -> None:
        """Get the latest summary data from the investments service."""
        pass