"""Validate command parser helpers and runner."""

from __future__ import annotations

import argparse
from typing import Callable

ValidateMain = Callable[[list[str] | None], int]


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--content-root",
        default=None,
        help="course repository root (default: current working directory)",
    )


def run(content_root: str | None, validate_main: ValidateMain) -> int:
    validate_argv: list[str] = []
    if content_root:
        validate_argv.extend(["--content-root", content_root])
    return validate_main(validate_argv)
