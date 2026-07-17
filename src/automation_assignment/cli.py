"""The package's single command-line entry point."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from automation_assignment.commands.readiness import wait_for_api
from automation_assignment.commands.write_summary import write_summary
from automation_assignment.config import get_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="automation-assignment")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("wait-for-api", help="Wait until the live Swagger endpoint is ready")

    summary = commands.add_parser("write-summary", help="Write aggregate gate results")
    summary.add_argument("--quality-exit", type=int, required=True)
    summary.add_argument("--functional-exit", type=int, required=True)
    summary.add_argument("--load-exit", type=int, required=True)
    summary.add_argument("--output", type=Path, default=Path("reports/run-summary.md"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "wait-for-api":
        return wait_for_api(get_settings())
    if args.command == "write-summary":
        return write_summary(
            quality_exit=args.quality_exit,
            functional_exit=args.functional_exit,
            load_exit=args.load_exit,
            output=args.output,
        )
    raise AssertionError(f"Unhandled command: {args.command}")
