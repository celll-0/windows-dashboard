"""Entry point. Run with: python main.py"""
import os
import sys
import cherrypy
from pathlib import Path
from loguru import logger

from dotenv import load_dotenv
load_dotenv()

# Static widget — the software scene-graph renders identically and avoids the
# GPU backend failing when launched early at startup. Overridable via the env.
os.environ.setdefault("QT_QUICK_BACKEND", "software")

# Make the `src` layout importable without an install step.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
# Make shared project-root packages (e.g. utils) importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dbrief_widget.app import Application
from dbrief_widget.signal_tether import run_signal_tether
from dbrief_widget.paths import LOGGING_CONFIG_PATH
from logging_conf import load_logging_config


def main() -> int:
    """Entry point for the dash-gui application."""
    load_logging_config(LOGGING_CONFIG_PATH)
    logger.info("dash-gui starting up")
    widget = Application()
    _signal_tether = run_signal_tether()
    exit_code = widget.run()
    logger.info("dash-gui shut down | exit_code={}", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
