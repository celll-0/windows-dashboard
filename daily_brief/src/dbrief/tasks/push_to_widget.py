from loguru import logger
from pydantic import PrivateAttr
from typing import Dict
from os import environ

from dbrief.config import TaskConfigs, URLs
from dbrief.exceptions import TaskExecutionError
from dbrief.scheduling.task import Task
from dbrief.services import PersistenceService, StoreLike
from dbrief.services.external_comms import post, wait_for_widget_running
from dbrief.constants import WIDGET_READY_TIMEOUT



class PushToWidgetTask(Task):
    _store: StoreLike = PersistenceService

    _name: str = PrivateAttr(default_factory=lambda: TaskConfigs["PUSH_TO_WIDGET"].name)

    def get_name(self) -> str:
        return self._name

    def execute(self) -> None:
        """Get the latest data for the caller task's store key and push it to the widget."""
        if not self._caller:
            raise ValueError("Cannot find task data. No caller task is set for this task.")

        if not self._caller.store_table_name or not self._caller.store_key:
            raise ValueError("No table name or key defined for the caller task.")

        if not self._caller.gui_type:
            raise ValueError("No GUI type defined for the caller task.")

        data = self._store.get_from_table(self._caller.store_table_name).get(self._caller.store_key)
        # only push to the GUI if data is present and not empty
        if not data:
            logger.warning(
                f"{self._caller.store_key} data is incomplete or contains None values. Skipping push to widget."
            )
            return

        if not wait_for_widget_running(deadline=WIDGET_READY_TIMEOUT):
            logger.warning("Widget is not running. Skipping push to widget.")
            return
        try:
            success = post(
                self._widget_ingest_url(),
                headers={"Authorization": f"Bearer {environ.get('KEL_GUI_API_TOKEN')}"},
                json={"type": self._caller.gui_type, "data": data},
                timeout=5,
            )
            if success:
                logger.success("Data pushed to dash gui successfully!")
            else:
                raise RuntimeError("Failed to push data to the widget.")
        except Exception as e:
            logger.error("An error occurred while pushing data to the widget")
            raise TaskExecutionError(
                "Failed to push data to the widget", task_name=self.get_name()
            ) from e

    def _widget_ingest_url(self) -> str:
        """Construct the URL for pushing data to the widget."""
        return f"{URLs['DASH_GUI'].base_url}{URLs['DASH_GUI'].endpoints.widget_ingest}"