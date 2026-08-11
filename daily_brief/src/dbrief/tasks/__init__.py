from dbrief.tasks.account_summary import FetchSummaryTask
from dbrief.tasks.push_to_widget import PushToWidgetTask
from dbrief.tasks.portfolio_positions import FetchPortfolioPositionsTask
from dbrief.tasks.new_feed import FetchNewsFeedTask
from dbrief.scheduling.task import Task

TASK_HANDLER_MAP: dict[str, type[Task]] = {
    "fetch_investment_summary": FetchSummaryTask,
    "push_to_widget": PushToWidgetTask,
    "fetch_portfolio_positions": FetchPortfolioPositionsTask,
    "fetch_news_feed": FetchNewsFeedTask,
}


__all__ = [
    "FetchSummaryTask",
    "PushToWidgetTask",
    "FetchPortfolioPositionsTask",
    "FetchNewsFeedTask",
    "TASK_HANDLER_MAP",
]