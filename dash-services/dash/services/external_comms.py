import time
import os
import socket

from loguru import logger
from typing import Dict, Optional

import requests
from requests.exceptions import RequestException


def send_api_request(
        method: str, 
        url: str, 
        **kwargs
    ) -> Optional[Dict]:
    try:
        logger.info(f"{method.upper()} - {url}")
        response = requests.request(
            method,
            url,
            **kwargs
        )
        if response.ok:
            return response.json()
        else:
            logger.warning(f"Request returned non-OK status: {response.reason} - {response.text}")
            return None

    except RequestException as e:
        logger.error(f"{method.upper()} request to {url} failed")
        raise e


def _is_running() -> bool:
    host = os.getenv("GUI_HOST", "127.0.0.1")
    port = int(os.getenv("GUI_PORT", "8001"))
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def wait_for_widget_running(deadline: float) -> bool:
    """Poll _is_running() until it returns True or the deadline passes."""
    while time.monotonic() < deadline:
        if _is_running():
            return True
        time.sleep(0.5)
    return _is_running()
