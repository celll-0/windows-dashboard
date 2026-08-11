"""kel-dash CLI: talk to the running Kel-dash widget's local control API.

Run via bin/kel-dash (POSIX) or bin/kel-dash.cmd (Windows), or directly:
    poetry run python dash-cli/main.py <command> [options]
"""
from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
EXE_PATH = REPO_ROOT / "dist" / "Kel-dash" / "Kel-dash.exe"
LOG_PATH = EXE_PATH.parent / "logs" / "kel-dash.log"
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build-gui-exe.ps1"

READY_TIMEOUT_SECONDS = 30

WIDGET_PORT = int(os.getenv("GUI_PORT", "8001"))

WIDGET_HOST = os.getenv("GUI_HOST", "127.0.0.1")

def _base_url() -> str:
    return f"http://{WIDGET_HOST}:{WIDGET_PORT}/control"


def _is_running() -> bool:
    try:
        with socket.create_connection((WIDGET_HOST, WIDGET_PORT), timeout=1):
            return True
    except OSError:
        return False


def _wait_for(target_running: bool, deadline: float) -> bool:
    """Poll _is_running() until it matches target_running or the deadline passes."""
    while time.monotonic() < deadline:
        if _is_running() == target_running:
            return True
        time.sleep(0.5)
    return _is_running() == target_running


def _headers() -> dict:
    token = os.getenv("KEL_DASH_CONTROL_TOKEN")
    if not token:
        print("KEL_DASH_CONTROL_TOKEN is not set (check your .env)", file=sys.stderr)
        sys.exit(1)
    return {"X-Kel-Dash-Token": token}


def _call(method: str, path: str, **kwargs) -> int:
    url = f"{_base_url()}/{path}"
    try:
        resp = requests.request(method, url, headers=_headers(), timeout=10, **kwargs)
    except requests.RequestException as exc:
        print(f"Could not reach Kel-dash at {url}: {exc}", file=sys.stderr)
        return 1

    try:
        body = resp.json()
    except ValueError:
        body = resp.text
    print(body)

    if not resp.ok:
        return 1
    return 0


def cmd_start(_args: argparse.Namespace) -> int:
    if _is_running():
        print("Kel-dash is already running")
        return 0

    if not EXE_PATH.exists():
        print(f"Kel-dash.exe not found at {EXE_PATH}", file=sys.stderr)
        print("Build it first: kel-dash build", file=sys.stderr)
        return 1

    # Force production path resolution in the launched exe -- without this it
    # inherits ENV=development from this CLI's own load_dotenv() call, which
    # makes the frozen exe resolve paths (logs, config) as if it were a dev
    # checkout instead of the dist folder. Same fix start.bat already applies.
    env = {**os.environ, "ENV": "production"}
    subprocess.Popen(
        [str(EXE_PATH)],
        env=env,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    print(f"Started {EXE_PATH}; waiting for it to come up...")
    if not _wait_for(True, time.monotonic() + READY_TIMEOUT_SECONDS):
        print("Timed out waiting for Kel-dash to become reachable", file=sys.stderr)
        return 1
    print("Kel-dash is up; triggering refresh")
    return _call("POST", "refresh")


def cmd_stop(_args: argparse.Namespace) -> int:
    return _call("POST", "stop")


def cmd_restart(_args: argparse.Namespace) -> int:
    rc = _call("POST", "restart")
    if rc != 0:
        return rc

    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    _wait_for(False, deadline)  # best-effort; fall through to the up-check regardless
    if not _wait_for(True, deadline):
        print("Timed out waiting for Kel-dash to come back up after restart", file=sys.stderr)
        return 1
    print("Kel-dash is back up; triggering refresh")
    return _call("POST", "refresh")


def cmd_refresh(_args: argparse.Namespace) -> int:
    return _call("POST", "refresh")


def cmd_snapshots(args: argparse.Namespace) -> int:
    params = {"since": args.since} if args.since else {}
    return _call("GET", "snapshots", params=params)


def cmd_build(_args: argparse.Namespace) -> int:
    if _is_running():
        print("Kel-dash is currently running -- stop it first (kel-dash stop) before rebuilding.", file=sys.stderr)
        print(r"PyInstaller can't overwrite dist\Kel-dash while the running exe holds files open there.", file=sys.stderr)
        return 1
    result = subprocess.run(
        ["powershell", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(BUILD_SCRIPT)],
        cwd=REPO_ROOT,
    )
    return result.returncode


def cmd_logs_show(_args: argparse.Namespace) -> int:
    if not LOG_PATH.exists():
        print(f"No log file at {LOG_PATH}", file=sys.stderr)
        return 1

    lines = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()

    if not (sys.stdout.isatty() and sys.stdin.isatty()):
        print("\n".join(lines))
        return 0

    page_size = max(shutil.get_terminal_size(fallback=(80, 24)).lines - 1, 1)
    for i in range(0, len(lines), page_size):
        print("\n".join(lines[i:i + page_size]))
        if i + page_size >= len(lines):
            print("\033[7m END \033[0m")
            break
        try:
            if input("-- More -- (Enter to continue, q to quit) ").strip().lower() == "q":
                break
        except (EOFError, KeyboardInterrupt):
            break
    return 0


def cmd_logs_attach(_args: argparse.Namespace) -> int:
    if not LOG_PATH.exists():
        print(f"No log file at {LOG_PATH} yet -- is the widget running?", file=sys.stderr)
        return 1

    print(f"Attached to {LOG_PATH} (Ctrl+C to detach)")
    f = open(LOG_PATH, "r", encoding="utf-8", errors="replace")
    f.seek(0, os.SEEK_END)
    pos = f.tell()
    try:
        while True:
            line = f.readline()
            if line:
                print(line, end="")
                pos = f.tell()
                continue
            if os.path.getsize(LOG_PATH) < pos:
                f.close()
                f = open(LOG_PATH, "r", encoding="utf-8", errors="replace")
                pos = 0
            time.sleep(0.5)
    except KeyboardInterrupt:
        print()
    finally:
        f.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="kel-dash", description="Control the running Kel-dash widget.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "start", help="Start the widget and refresh once it's up (no-op if already running)"
    ).set_defaults(func=cmd_start)
    subparsers.add_parser("stop", help="Stop the running widget").set_defaults(func=cmd_stop)
    subparsers.add_parser(
        "restart", help="Restart the widget and refresh once it's back up"
    ).set_defaults(func=cmd_restart)
    subparsers.add_parser("refresh", help="Trigger an immediate data refresh").set_defaults(func=cmd_refresh)
    subparsers.add_parser("build", help="Rebuild Kel-dash.exe (refuses while it's running)").set_defaults(func=cmd_build)

    snapshots_parser = subparsers.add_parser("snapshots", help="List stored snapshots")
    snapshots_parser.add_argument("--since", help="ISO-8601 timestamp; only snapshots at/after this time")
    snapshots_parser.set_defaults(func=cmd_snapshots)

    logs_parser = subparsers.add_parser("logs", help="Inspect the widget's log file")
    logs_subparsers = logs_parser.add_subparsers(dest="logs_command", required=True)
    logs_subparsers.add_parser("show", help="Page through the full log file").set_defaults(func=cmd_logs_show)
    logs_subparsers.add_parser(
        "attach", help="Follow new log lines live (Ctrl+C to detach)"
    ).set_defaults(func=cmd_logs_attach)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
