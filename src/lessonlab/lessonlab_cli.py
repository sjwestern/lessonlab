"""Top-level lessonlab CLI."""

from __future__ import annotations

import argparse
import pathlib
import sys

from .cli import main as serve_main
from .paths import Paths
from .scaffold import scaffold_lesson
from .validation import main as validate_main


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lessonlab")
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Run lesson server")
    serve_parser.add_argument("args", nargs=argparse.REMAINDER)

    validate_parser = subparsers.add_parser("validate", help="Validate answer files")
    validate_parser.add_argument("args", nargs=argparse.REMAINDER)

    scaffold_parser = subparsers.add_parser("scaffold", help="Scaffold project files")
    scaffold_subparsers = scaffold_parser.add_subparsers(dest="scaffold_command")

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

    return parser


def _strip_remainder_marker(values: list[str]) -> list[str]:
    if values and values[0] == "--":
        return values[1:]
    return values


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "serve":
        return serve_main(_strip_remainder_marker(args.args))

    if args.command == "validate":
        return validate_main(_strip_remainder_marker(args.args))

    if args.command == "scaffold" and args.scaffold_command == "lesson":
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

    parser.print_help(sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
