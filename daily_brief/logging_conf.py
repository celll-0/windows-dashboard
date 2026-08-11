from pathlib import Path
from loguru import logger
from loguru_config import LoguruConfig


def load_logging_config(logging_config: Path) -> None:
    # Initialise the logger with the configuration from logging.yml
    try:
        LoguruConfig.load(logging_config)
        logger.info("Application logger configured successfully and running")
    except Exception as e:
        logger.warning(f"Failed to load logging configuration. Using default logger configuration. Error: {e}")