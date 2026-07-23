"""Top-level lessonlab CLI."""

from __future__ import annotations

import argparse
import sys

from .commands.scaffold import add_arguments as add_scaffold_arguments
from .commands.scaffold import run as _run_scaffold
from .commands.serve import add_arguments as add_serve_arguments
from .commands.serve import run as _run_serve
from .commands.validate import add_arguments as add_validate_arguments
from .commands.validate import run as _run_validate_command
from .validation import main as validate_main


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lessonlab")
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Run lesson server")
    add_serve_arguments(serve_parser)

    validate_parser = subparsers.add_parser("validate", help="Validate answer files")
    add_validate_arguments(validate_parser)

    scaffold_parser = subparsers.add_parser("scaffold", help="Scaffold project files")
    add_scaffold_arguments(scaffold_parser)

    return parser


def _run_validate(content_root: str | None) -> int:
    return _run_validate_command(content_root, validate_main)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "serve":
        return _run_serve(args)

    if args.command == "validate":
        return _run_validate(args.content_root)

    if args.command == "scaffold" and args.scaffold_command == "lesson":
        return _run_scaffold(args)

    parser.print_help(sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
