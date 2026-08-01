from dash.tasks.account_summary import FetchSummaryTask
from dash.tasks.push_to_widget import PushToWidgetTask
from dash.tasks.portfolio_positions import FetchPortfolioPositionsTask
from dash.scheduling.task import Task

TASK_HANDLER_MAP: dict[str, type[Task]] = {
    "fetch_investment_summary": FetchSummaryTask,
    "push_to_widget": PushToWidgetTask,
    "fetch_portfolio_positions": FetchPortfolioPositionsTask,
}


__all__ = [
    "FetchSummaryTask",
    "PushToWidgetTask",
    "FetchPortfolioPositionsTask",
    "TASK_HANDLER_MAP",
]