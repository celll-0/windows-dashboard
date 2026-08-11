import sys
from pathlib import Path
from loguru import logger
from loguru_config import LoguruConfig

from dbrief_widget.paths import LOG_DIR


def load_logging_config(logging_config: Path) -> None:
    # Initialise the logger with the configuration from logging.yml
    try:
        LoguruConfig.load(logging_config)
        logger.info("Application logger configured successfully and running")
    except Exception as e:
        logger.warning(f"Failed to load logging configuration. Using default logger configuration. Error: {e}")

    if getattr(sys, "frozen", False):
        # The packaged EXE runs windowed (console=False), so the stdout/stderr
        # sinks configured above go nowhere -- write to a file instead. This
        # only fires in the frozen build; dev runs are unaffected.
        logger.add(
            LOG_DIR / "dailybrief.log",
            level="DEBUG",
            format="[{time:YYYY-MM-DD HH:mm:ss.SSS}] {level.name:<8} | {name}:{function}:{line} | {message}",
            rotation="5 MB",
            retention="2 weeks",
            enqueue=True,
            backtrace=True,
        )