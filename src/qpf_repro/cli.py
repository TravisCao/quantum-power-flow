"""Command-line interface for the reproduction workflow."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from .experiments import reproduce_all


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reproduce the quantum power-flow experiments.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    reproduce = subparsers.add_parser("all", help="Run all experiments.")
    reproduce.add_argument("--output", default="results", help="Output directory.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "all":
        reproduce_all(arguments.output)
    return 0
