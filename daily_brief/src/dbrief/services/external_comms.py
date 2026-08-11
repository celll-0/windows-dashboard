import time
import os
import socket

from loguru import logger
from typing import Dict, Optional

from curl_cffi import requests
from curl_cffi.requests.exceptions import RequestException


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


def create_session(headers: Optional[Dict[str, str]] = None) -> requests.Session:
    session = requests.Session(impersonate="firefox147")
    if headers:
        session.headers.update(headers)
    return session


