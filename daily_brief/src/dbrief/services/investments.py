from os import environ
from typing import Dict, Optional

from loguru import logger
from requests.exceptions import RequestException

from .external_comms import get
from ..config import URLs


class InvestmentDataService:
    def get_summary(self) -> Optional[Dict]:
        # Build the full endpoint URL for the account summary
        url = f"{URLs['T212'].base_url}{URLs['T212'].endpoints.summary}"
        _username = environ.get('TRADING212_KEY_ID')
        _password = environ.get('TRADING212_AUTH_KEY')

        # Guard against missing API key before making any network calls
        if _username is None or _password is None:
            raise RuntimeError(
                "investment API credentials are required. Please check they are loaded from environment correctly"
            )

        try:
            logger.info(f"Fetching account summary from {url}")
            summary_data = get(
                url,
                auth=(_username, _password),
                timeout=5,
            )
            # TODO: FIX - task exits to scheduler with a success status on whether the request is successful or not
            if summary_data:
                logger.success("Account summary data fetched successfully!")
            return summary_data
        except RequestException as e:
            logger.error("An error occurred while fetching trading account summary")
            raise e


    def get_positions(self) -> Optional[Dict]:
        # Build the full endpoint URL for the account positions
        url = f"{URLs['T212'].base_url}{URLs['T212'].endpoints.positions}"
        _username = environ.get('TRADING212_KEY_ID')
        _password = environ.get('TRADING212_AUTH_KEY')

        # Guard against missing API key before making any network calls
        if _username is None or _password is None:
            raise RuntimeError(
                "investment API credentials are required. Please check they are loaded from environment correctly"
            )

        try:
            logger.info(f"Fetching account positions from {url}")
            positions_data = get(
                url,
                auth=(_username, _password),
                timeout=5,
            )
            if positions_data:
                logger.success("Account positions data fetched successfully!")
            return positions_data
        except RequestException as e:
            logger.error("An error occurred while fetching trading account positions")
            raise e

InvestmentsService = InvestmentDataService()