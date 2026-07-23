"""Filesystem layout used by the lesson runtime.

Two roots are distinguished:

- ``framework_root`` -- where the packaged assets and JSON Schema live. Owned
  by this package and shipped with it.
- ``content_root`` -- where the course keeps ``lessons/``, ``reference/``, and
  ``learning-state/``. Owned by the course repository.

Every module that touches the filesystem receives a ``Paths`` instance rather
than reading module-level globals. This makes it trivial to point the runtime
at a temporary directory in tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
# Package lives at ``lessonlab/src/lessonlab``; the framework root that ships
# ``assets/`` and ``schemas/`` is two levels up.
DEFAULT_FRAMEWORK_ROOT = PACKAGE_DIR.parent.parent


@dataclass(frozen=True)
class Paths:
    """Resolved filesystem locations for one running server."""

    content_root: Path
    framework_root: Path = DEFAULT_FRAMEWORK_ROOT

    @property
    def lessons_dir(self) -> Path:
        return self.content_root / "lessons"

    @property
    def state_dir(self) -> Path:
        return self.content_root / "learning-state"

    @property
    def answers_dir(self) -> Path:
        return self.state_dir / "answers"

    @property
    def progress_file(self) -> Path:
        return self.state_dir / "progress.json"

    @property
    def framework_assets_dir(self) -> Path:
        return self.framework_root / "assets"

    @property
    def schema_path(self) -> Path:
        return self.framework_root / "schemas" / "answer.schema.json"

    def answer_file(self, lesson_id: str) -> Path:
        return self.answers_dir / f"{lesson_id}.json"
