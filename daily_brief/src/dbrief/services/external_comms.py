import time
import socket

from loguru import logger
from typing import Dict, Optional

from curl_cffi import requests
from curl_cffi.requests.exceptions import RequestException

from dbrief.constants import GUI_HOST, GUI_PORT


def get(url: str, session: Optional[requests.Session] = None, **kwargs) -> Optional[Dict]:
    try:
        req = session if session is not None else requests
        response = req.get(
            url,
            **kwargs
        )
        if response.ok:
            return response.json()
        else:
            logger.warning(f"Request returned non-OK status: {response.reason} - {response.text}")
            return None

    except RequestException as e:
        logger.error(f"GET/ {url} - request failed")
        raise e


def post(url: str, session: Optional[requests.Session] = None, **kwargs) -> Optional[Dict]:
    try:
        req = session if session is not None else requests
        response = req.post(
            url,
            **kwargs
        )
        if response.ok:
            return response.json()
        else:
            logger.warning(f"Request returned non-OK status: {response.reason} - {response.text}")
            return None

    except RequestException as e:
        logger.error(f"POST/ {url} - request failed")
        raise e


def _is_running() -> bool:
    try:
        with socket.create_connection((GUI_HOST, GUI_PORT), timeout=1):
            return True
    except OSError:
        return False


def wait_for_widget_running(timeout: float) -> bool:
    """Poll _is_running() until it returns True or timeout seconds elapse."""
    logger.info(f"Waiting for widget to be running")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _is_running():
            return True
        time.sleep(0.5)
    return _is_running()


def create_session(headers: Optional[Dict[str, str]] = None) -> requests.Session:
    session = requests.Session(impersonate="firefox147")
    if headers:
        session.headers.update(headers)
    return session


