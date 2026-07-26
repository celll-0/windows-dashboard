"""kel-dash CLI: talk to the running Kel-dash widget's local control API.

Run via bin/kel-dash (POSIX) or bin/kel-dash.cmd (Windows), or directly:
    poetry run python dash-cli/main.py <command> [options]
"""
from __future__ import annotations

import argparse
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()


def _base_url() -> str:
    host = os.getenv("GUI_HOST", "127.0.0.1")
    port = os.getenv("GUI_PORT", "8001")
    return f"http://{host}:{port}/control"


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


def cmd_stop(_args: argparse.Namespace) -> int:
    return _call("POST", "stop")


def cmd_restart(_args: argparse.Namespace) -> int:
    return _call("POST", "restart")


def cmd_refresh(_args: argparse.Namespace) -> int:
    return _call("POST", "refresh")


def cmd_snapshots(args: argparse.Namespace) -> int:
    params = {"since": args.since} if args.since else {}
    return _call("GET", "snapshots", params=params)


def main() -> int:
    parser = argparse.ArgumentParser(prog="kel-dash", description="Control the running Kel-dash widget.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("stop", help="Stop the running widget").set_defaults(func=cmd_stop)
    subparsers.add_parser("restart", help="Restart the widget (relaunches itself)").set_defaults(func=cmd_restart)
    subparsers.add_parser("refresh", help="Trigger an immediate data refresh").set_defaults(func=cmd_refresh)

    snapshots_parser = subparsers.add_parser("snapshots", help="List stored snapshots")
    snapshots_parser.add_argument("--since", help="ISO-8601 timestamp; only snapshots at/after this time")
    snapshots_parser.set_defaults(func=cmd_snapshots)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
