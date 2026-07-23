"""Atomic JSON read/write for the two state files.

The runtime is single-process and serves a single learner, so a
:class:`threading.Lock` shared across all writes is enough to make the
progress + per-lesson answer files consistent.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from .paths import Paths


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_atomic(path: Path, value: Any) -> None:
    """Write JSON via a temp file + rename so readers never see a partial file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(
        f"{json.dumps(value, indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


class StateStore:
    """Owns access to the progress file and per-lesson answer files."""

    def __init__(self, paths: Paths, lock: threading.Lock | None = None) -> None:
        self._paths = paths
        self._lock = lock or threading.Lock()

    @property
    def lock(self) -> threading.Lock:
        return self._lock

    def read_progress(self, default: Any) -> Any:
        return read_json(self._paths.progress_file, default)

    def write_progress(self, value: Any) -> None:
        write_json_atomic(self._paths.progress_file, value)

    def read_answers(self, lesson_id: str, default: Any) -> Any:
        return read_json(self._paths.answer_file(lesson_id), default)

    def write_answers(self, lesson_id: str, value: Any) -> None:
        write_json_atomic(self._paths.answer_file(lesson_id), value)
