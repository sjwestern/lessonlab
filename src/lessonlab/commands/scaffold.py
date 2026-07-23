"""Scaffold command parser helpers and runner."""

from __future__ import annotations

import argparse
import pathlib
import sys

from ..paths import Paths
from ..scaffold import scaffold_lesson


def add_arguments(parser: argparse.ArgumentParser) -> None:
    scaffold_subparsers = parser.add_subparsers(dest="scaffold_command")

    lesson_parser = scaffold_subparsers.add_parser(
        "lesson", help="Create a lesson HTML file"
    )
    lesson_parser.add_argument("--content-root", default=None)
    lesson_parser.add_argument("--slug", required=True)
    lesson_parser.add_argument("--mode", choices=("concept", "build"), default="concept")
    lesson_parser.add_argument("--id", default=None)
    lesson_parser.add_argument("--title", default=None)
    lesson_parser.add_argument("--response-id", action="append", default=None)
    lesson_parser.add_argument("--force", action="store_true")


def run(args: argparse.Namespace) -> int:
    content_root = pathlib.Path(args.content_root or ".").resolve()
    paths = Paths(content_root=content_root)

    try:
        path = scaffold_lesson(
            paths=paths,
            slug=args.slug,
            mode=args.mode,
            lesson_id=args.id,
            force=args.force,
            title=args.title,
            response_ids=args.response_id,
        )
    except (ValueError, FileExistsError) as error:
        print(f"lessonlab: {error}", file=sys.stderr)
        return 1

    print(path.relative_to(paths.content_root).as_posix())
    return 0
