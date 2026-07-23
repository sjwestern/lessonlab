"""Serve command runtime and parser helpers."""

from __future__ import annotations

import argparse
import http.server
import pathlib
import sys
import urllib.parse

from ..http_app import make_handler_class
from ..lessons import LessonIndex, resolve_lesson
from ..paths import Paths
from ..service import LessonService
from ..state import StateStore


def _create_server(
    bind_address: str,
    preferred_port: int,
    handler_class: type[http.server.BaseHTTPRequestHandler],
) -> http.server.ThreadingHTTPServer:
    for port in range(preferred_port, preferred_port + 20):
        try:
            return http.server.ThreadingHTTPServer((bind_address, port), handler_class)
        except OSError:
            continue
    raise OSError(f"No available port from {preferred_port} to {preferred_port + 19}.")


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--content-root",
        default=None,
        help="course repository root (default: current working directory)",
    )
    parser.add_argument(
        "--lesson",
        default="latest",
        help="lesson number, filename, or 'latest' (default: latest)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="first port to try (default: 8000)",
    )
    parser.add_argument(
        "--bind",
        default="127.0.0.1",
        help="address to bind (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list available lessons and exit",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lessonlab serve",
        description="Serve a local lesson course to VS Code Simple Browser.",
    )
    add_arguments(parser)
    return parser


def run(args: argparse.Namespace) -> int:
    content_root = pathlib.Path(args.content_root or ".").resolve()
    paths = Paths(content_root=content_root)
    index = LessonIndex(paths.lessons_dir)

    if args.list:
        for lesson_path in index.paths():
            print(lesson_path.name)
        return 0

    problems = index.check_filenames()
    if problems:
        for problem in problems:
            print(f"lessonlab serve: {problem}", file=sys.stderr)
        return 1

    try:
        lesson_path = resolve_lesson(index, args.lesson)
    except ValueError as error:
        print(f"lessonlab serve: {error}", file=sys.stderr)
        return 1

    store = StateStore(paths)
    service = LessonService(store, index)
    handler_class = make_handler_class(service, paths)

    try:
        server = _create_server(args.bind, args.port, handler_class)
    except OSError as error:
        print(f"lessonlab serve: {error}", file=sys.stderr)
        return 1

    relative_lesson = lesson_path.relative_to(paths.content_root).as_posix()
    lesson_url = urllib.parse.quote(relative_lesson, safe="/")
    port = server.server_address[1]

    print("Lesson server is running.")
    print(f"Open in VS Code Simple Browser: http://127.0.0.1:{port}/{lesson_url}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nLesson server stopped.")
    finally:
        server.server_close()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run(args)
