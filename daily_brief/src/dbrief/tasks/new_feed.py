from typing import Optional
from loguru import logger
from pydantic import PrivateAttr

from dbrief.config import TaskConfigs
from dbrief.services import (
    NewsService,
    GroundNewsService,
)
from dbrief.services.news import Event
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
        if not self.store_key:
            raise ValueError("Store key is not defined for storing news feed.")
        
        subscribed_interests = self.newsService.get_subscribed()
        if subscribed_interests:
            logger.info(f"Fetching news for subscribed interests:\n{'\n'.join([f'- {interest.name}' for interest in subscribed_interests])}")
            feed = {}
            for interest in subscribed_interests:
                story_ids = self.newsService.get_interest_top_stories(interest.id)
                feed[interest.name] = self._get_feed_events(story_ids)

            if not any(feed.values()):
                logger.warning("No stories found for any subscribed interests.")
            self._data[self.store_key] = feed
            

    def _get_feed_events(self, story_ids: list[str]) -> list[Event]:
        """Fetch a batch of stories with given ids"""
        stories = []
        for story_id in story_ids:
            story = self.newsService.get_story(story_id)
            stories.append(story.model_dump(mode="python"))
        return stories
