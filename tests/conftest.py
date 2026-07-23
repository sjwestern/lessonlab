"""Shared pytest fixtures.

Every test that needs the runtime spins up a fresh temporary content root so
tests can run in parallel and never touch the real course files.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from lessonlab.lessons import LessonIndex
from lessonlab.paths import Paths
from lessonlab.service import LessonService
from lessonlab.state import StateStore


CONCEPT_LESSON_NAME = "0001-example-topic.concept.html"
BUILD_LESSON_NAME = "0002-example-artifact.build.html"


def _minimal_lesson_html(lesson_id: str) -> str:
    return f"""<!doctype html><html><body>
<main data-lesson-id="{lesson_id}"></main>
</body></html>
"""


@pytest.fixture()
def content_root(tmp_path: Path) -> Path:
    lessons = tmp_path / "lessons"
    lessons.mkdir()
    (lessons / CONCEPT_LESSON_NAME).write_text(_minimal_lesson_html("0001"), encoding="utf-8")
    (lessons / BUILD_LESSON_NAME).write_text(_minimal_lesson_html("0002"), encoding="utf-8")
    return tmp_path


@pytest.fixture()
def paths(content_root: Path) -> Paths:
    return Paths(content_root=content_root)


@pytest.fixture()
def index(paths: Paths) -> LessonIndex:
    return LessonIndex(paths.lessons_dir)


@pytest.fixture()
def service(paths: Paths, index: LessonIndex) -> LessonService:
    store = StateStore(paths, lock=threading.Lock())
    ticks = iter(range(1, 10_000))

    def fake_clock() -> str:
        return f"2026-01-01T00:00:{next(ticks):02d}Z"

    return LessonService(store, index, clock=fake_clock)
