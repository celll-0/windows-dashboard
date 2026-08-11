
from os import getenv
from pathlib import Path

is_prod = getenv('ENV') == 'production'

pkg_depth_from_proj_root = 1 if is_prod else 2

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[pkg_depth_from_proj_root-1]

if is_prod:
    ROOT_DIR = PROJECT_ROOT
else:
    ROOT_DIR = PROJECT_ROOT.parent

LOGGING_CONFIG_PATH = ROOT_DIR / 'logging.yml'
DB_PATH = PROJECT_ROOT / 'store.json'