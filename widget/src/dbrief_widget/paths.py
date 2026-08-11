"""Central filesystem locations, resolved relative to the project root.

`config.py/paths.py` live at ``src/investment_widget/`` so the project root is
two levels up. Keeping every path in one place means nothing else has to know
how the repo is laid out.
"""
from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = PACKAGE_DIR.parents[1]

ROOT_DIR = PROJECT_ROOT.parent

LOGGING_CONFIG_PATH = ROOT_DIR / "logging.yml"
LOG_DIR = ROOT_DIR / "logs"
CONFIG_PATH = PROJECT_ROOT / "config.yml"
DB_PATH = PROJECT_ROOT / "snapshots.db"
UI_DIR = PACKAGE_DIR / "ui"
MAIN_QML = UI_DIR / "Main.qml"
