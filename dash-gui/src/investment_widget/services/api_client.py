"""HTTP access to the local investments endpoint."""
from __future__ import annotations

import time

import requests
import json
from loguru import logger


class ApiClient:
    def __init__(self, base_url: str, timeout: int = 10) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        logger.debug("ApiClient configured | base_url={} timeout={}s", base_url, timeout)

    def fetch(self, path: str) -> dict:
        """GET ``{base_url}/{path}`` and return the decoded JSON dict.

            Raises ``requests.RequestException`` on failure.
        """
        url = f"{self._base_url}/{path.lstrip('/')}"
        logger.debug("GET {}", url)
        t0 = time.monotonic()
        resp = self._session.get(url, timeout=self._timeout)
        resp.raise_for_status()
        elapsed_ms = (time.monotonic() - t0) * 1000
        logger.debug("Response received in {:.0f}ms ({} bytes)", elapsed_ms, len(resp.content))
        return resp.json()