from loguru import logger
from pydantic import PrivateAttr
from typing import Dict
from os import environ

from dash.config import TaskConfigs, URLs
from dash.scheduling.task import Task
from dash.services import PersistenceService, StoreLike
from dash.services.external_comms import send_api_request





class PushToWidgetTask(Task):
    _store: StoreLike = PersistenceService

    _name: str = PrivateAttr(default_factory=lambda: TaskConfigs["PUSH_TO_WIDGET"].name)

    def get_name(self) -> str:
        return self._name

    def execute(self) -> None:
        """Get the latest summary data from the store and push it to the widget."""
        if not self._caller:
            raise ValueError("Cannot find task data. No caller task is set for this task.")
        
        if not self._caller.store_table_name or not self._caller.store_key:
            raise ValueError("No table name or key defined for the caller task.")
        data = {
            k: v
            for k, v in self._store.get_from_table(self._caller.store_table_name).items()
            if k == self._caller.store_key
        }
        # only push to the GUI if all values are present and not None
        if not all(data.values()):
            logger.warning(
                f"{self._caller.store_key} data is incomplete or contains None values. Skipping push to widget."
            )
            return
        try:
            success = send_api_request(
                "POST",
                self._widget_ingest_url(),
                headers={"Authorization": f"Bearer {environ.get('KEL_GUI_API_TOKEN')}"},
                data=data,
                timeout=5,
            )
            if success:
                logger.success("Data pushed to dash gui successfully!")
            else:
                raise RuntimeError("Failed to push data to the widget.")
        except Exception as e:
            logger.error("An error occurred while pushing data to the widget")
            raise e

    def _widget_ingest_url(self) -> str:
        """Construct the URL for pushing data to the widget."""
        return f"{URLs['DASH_GUI'].base_url}{URLs['DASH_GUI'].endpoints.widget_ingest}"