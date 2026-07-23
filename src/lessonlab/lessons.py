"""Lesson-file discovery and the filename convention.

Filenames encode the lesson mode: ``NNNN-slug.(concept|build).html``. The
:class:`LessonIndex` caches directory scans so request handlers do not re-glob
the disk on every call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


LESSON_FILENAME_RE = re.compile(
    r"^(?P<id>[0-9]{4})-(?P<slug>[a-z0-9][a-z0-9-]*)\.(?P<mode>concept|build)\.html$"
)
LESSON_MODES = ("concept", "build")


@dataclass(frozen=True)
class LessonFile:
    """One discovered lesson HTML file."""

    id: str
    slug: str
    mode: str
    path: Path


def parse_lesson_filename(name: str) -> LessonFile | None:
    match = LESSON_FILENAME_RE.match(name)
    if match is None:
        return None
    return LessonFile(
        id=match.group("id"),
        slug=match.group("slug"),
        mode=match.group("mode"),
        path=Path(name),
    )


class LessonIndex:
    """Cached view of the ``lessons/`` directory.

    Call :meth:`refresh` to invalidate the cache. The runtime refreshes at
    startup and never during a request; the number of lessons is small enough
    that a stale index between edits is a non-issue.
    """

    def __init__(self, lessons_dir: Path) -> None:
        self._lessons_dir = lessons_dir
        self._by_id: dict[str, LessonFile] | None = None

    def refresh(self) -> None:
        self._by_id = None

    def _load(self) -> dict[str, LessonFile]:
        if self._by_id is not None:
            return self._by_id
        by_id: dict[str, LessonFile] = {}
        if self._lessons_dir.exists():
            for path in sorted(self._lessons_dir.glob("[0-9][0-9][0-9][0-9]-*.html")):
                parsed = parse_lesson_filename(path.name)
                if parsed is None:
                    continue
                by_id.setdefault(
                    parsed.id,
                    LessonFile(id=parsed.id, slug=parsed.slug, mode=parsed.mode, path=path),
                )
        self._by_id = by_id
        return by_id

    def ids(self) -> list[str]:
        return sorted(self._load().keys())

    def paths(self) -> list[Path]:
        return [lesson.path for lesson in self._load().values()]

    def get(self, lesson_id: str) -> LessonFile | None:
        return self._load().get(lesson_id)

    def mode_for(self, lesson_id: str) -> str | None:
        lesson = self.get(lesson_id)
        return lesson.mode if lesson else None

    def check_filenames(self) -> list[str]:
        """Return human-readable problems with lesson filenames.

        The scan here is intentional and uncached: it must see every filename,
        including ones that fail to match the pattern.
        """

        problems: list[str] = []
        seen_ids: set[str] = set()
        if not self._lessons_dir.exists():
            return problems
        for path in sorted(self._lessons_dir.glob("[0-9][0-9][0-9][0-9]-*.html")):
            parsed = parse_lesson_filename(path.name)
            if parsed is None:
                problems.append(
                    f"lesson filename must match NNNN-slug.(concept|build).html: {path.name}"
                )
                continue
            if parsed.id in seen_ids:
                problems.append(f"duplicate lesson id: {parsed.id}")
            seen_ids.add(parsed.id)
        return problems


def resolve_lesson(index: LessonIndex, requested: str) -> Path:
    """Map a CLI argument (``latest``, an id, a stem, or a filename) to a path."""

    paths = index.paths()
    if not paths:
        raise ValueError("No lessons found under the content root.")

    if requested == "latest":
        return paths[-1]

    lesson_number = requested.zfill(4)
    matches: list[Path] = []
    for path in paths:
        if (
            path.name == requested
            or path.stem == requested
            or path.name.startswith(f"{lesson_number}-")
        ):
            matches.append(path)
    if len(matches) != 1:
        raise ValueError(f"Could not find one lesson matching '{requested}'.")
    return matches[0]
