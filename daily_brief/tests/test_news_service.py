from loguru import logger
from dbrief.services import NewsService
from dbrief.services.news import Interest


def test_get_subscribed_returns_list_of_interests():
    result = NewsService.get_subscribed()
    logger.debug(f"Subscribed topics: {result}")
    assert isinstance(result, list)
    assert all(isinstance(item, Interest) for item in result)