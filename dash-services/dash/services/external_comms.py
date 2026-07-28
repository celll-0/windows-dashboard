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

