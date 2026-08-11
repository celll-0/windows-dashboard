# DailyBrief.spec
# Build with: pyinstaller DailyBrief.spec --noconfirm --clean
# (invoked by scripts/build-gui-exe.ps1, which resolves the Poetry venv first)
import os
from PyInstaller.utils.hooks import collect_all, copy_metadata

# --- Bundled read-only resources -------------------------------------------
datas = [
    ("widget/src/dbrief_widget/ui", "dbrief_widget/ui"),
]
binaries = []
hiddenimports = [
    # dbrief_widget's own subpackages (defensive; pathex below is what
    # actually lets PyInstaller find them on disk)
    "dbrief_widget",
    "dbrief_widget.bridge",
    "dbrief_widget.data",
    "dbrief_widget.presentation",
    "dbrief_widget.services",
    # top-level module PyInstaller can only find via pathex
    "logging_conf",
    # utils.logging is loaded dynamically at runtime via the
    # `ext://utils.logging._stdout_filter` string in logging.yml -- this is
    # invisible to PyInstaller's static import scanner, so it must be
    # declared explicitly or the frozen app silently falls back to the
    # default loguru logger (see logging_conf.load_logging_config).
    "utils",
    "utils.logging",
    "loguru_config",
]

# --- CherryPy/Cheroot: bundle everything + their dist-info metadata --------
# CherryPy/Cheroot read their own installed-package metadata via
# importlib.metadata at import time. A frozen build has no dist-info on disk
# by default, so without copy_metadata() you get
# "importlib.metadata.PackageNotFoundError: No package metadata was found
# for cherrypy" at first launch.
for pkg in ("cherrypy", "cheroot"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    datas += copy_metadata(pkg)
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

a = Analysis(
    ["widget/main.py"],
    pathex=[
        os.path.join("widget", "src"),     # -> dbrief_widget package
        "widget",                          # -> logging_conf.py
        ".",                                # -> utils/ package at repo root
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DailyBrief",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="DailyBrief",
)
