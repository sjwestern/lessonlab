"""Init command parser helpers and runner."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--content-root",
        default=None,
        help="course repository root (default: current working directory)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite learning-state/progress.json if it already exists",
    )


def _default_progress() -> dict[str, object]:
    return {
        "version": 1,
        "currentLesson": None,
        "updatedAt": None,
        "lessons": {},
    }


def run(args: argparse.Namespace) -> int:
    content_root = pathlib.Path(args.content_root or ".").resolve()
    content_root.mkdir(parents=True, exist_ok=True)

    created: list[pathlib.Path] = []

    for relative_dir in ("lessons", "reference", "learning-state/answers"):
        path = content_root / relative_dir
        if not path.exists():
            created.append(path)
        path.mkdir(parents=True, exist_ok=True)

    progress_path = content_root / "learning-state" / "progress.json"
    if progress_path.exists() and not args.force:
        print(
            "lessonlab init: progress file already exists "
            f"({progress_path.relative_to(content_root).as_posix()}); use --force to overwrite",
            file=sys.stderr,
        )
        return 1

    progress_path.write_text(
        f"{json.dumps(_default_progress(), indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )
    created.append(progress_path)

    for path in created:
        print(path.relative_to(content_root).as_posix())

    return 0
