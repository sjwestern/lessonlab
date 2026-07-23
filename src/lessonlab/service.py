"""Use-case layer.

Everything above :class:`LessonService` speaks in domain terms; everything
below (HTTP handler, CLI) treats the service as an opaque object with four
methods. This is where the concept/build state machine lives.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from .lessons import LessonIndex
from .state import StateStore
from .validation import ValidationError, validate_answers, validate_artifacts


class LessonNotFoundError(LookupError):
    """Raised when the caller references a lesson id that does not exist."""


def _default_clock() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class LessonService:
    def __init__(
        self,
        store: StateStore,
        index: LessonIndex,
        clock: Callable[[], str] = _default_clock,
    ) -> None:
        self._store = store
        self._index = index
        self._clock = clock

    # -- reads -----------------------------------------------------------------

    def get_progress(self) -> dict[str, Any]:
        with self._store.lock:
            return self._store.read_progress(self._default_progress())

    def get_answers(self, lesson_id: str) -> dict[str, Any]:
        self._require_known(lesson_id)
        with self._store.lock:
            return self._store.read_answers(lesson_id, self._default_answers(lesson_id))

    # -- writes ----------------------------------------------------------------

    def save_draft(
        self,
        lesson_id: str,
        answers_payload: Any,
        artifacts_payload: Any,
    ) -> dict[str, Any]:
        return self._save(lesson_id, answers_payload, artifacts_payload, submit=False)

    def submit(
        self,
        lesson_id: str,
        answers_payload: Any,
        artifacts_payload: Any,
    ) -> dict[str, Any]:
        return self._save(lesson_id, answers_payload, artifacts_payload, submit=True)

    # -- internals -------------------------------------------------------------

    def _require_known(self, lesson_id: str) -> None:
        if self._index.get(lesson_id) is None:
            raise LessonNotFoundError(f"unknown lesson: {lesson_id}")

    def _save(
        self,
        lesson_id: str,
        answers_payload: Any,
        artifacts_payload: Any,
        *,
        submit: bool,
    ) -> dict[str, Any]:
        self._require_known(lesson_id)
        mode = self._index.mode_for(lesson_id) or "concept"

        answers = validate_answers(answers_payload)
        artifacts = self._validate_artifacts_for_mode(mode, artifacts_payload, submit=submit)

        timestamp = self._clock()
        status = "submitted" if submit else "in-progress"
        submitted_at = timestamp if submit else None

        answer_state = {
            "version": 1,
            "lesson": lesson_id,
            "mode": mode,
            "status": status,
            "updatedAt": timestamp,
            "submittedAt": submitted_at,
            "answers": answers,
            "artifacts": artifacts,
        }

        with self._store.lock:
            self._store.write_answers(lesson_id, answer_state)

            progress = self._store.read_progress(self._default_progress())
            lessons = progress.setdefault("lessons", {})
            lesson_progress = lessons.setdefault(
                lesson_id,
                {
                    "status": "not-started",
                    "startedAt": None,
                    "submittedAt": None,
                    "completedAt": None,
                },
            )
            lesson_progress["status"] = status
            lesson_progress["startedAt"] = lesson_progress.get("startedAt") or timestamp
            lesson_progress["submittedAt"] = submitted_at
            lesson_progress.setdefault("completedAt", None)
            progress["currentLesson"] = lesson_id
            progress["updatedAt"] = timestamp
            self._store.write_progress(progress)

        return answer_state

    def _validate_artifacts_for_mode(
        self,
        mode: str,
        artifacts_payload: Any,
        *,
        submit: bool,
    ) -> dict[str, Any] | None:
        if mode == "build":
            if submit:
                if artifacts_payload is None:
                    raise ValidationError(
                        "build lessons require an artifacts object on submit"
                    )
                return validate_artifacts(artifacts_payload)
            if artifacts_payload is None:
                return None
            return validate_artifacts(artifacts_payload)

        # concept mode
        if artifacts_payload is not None:
            raise ValidationError("concept lessons must not include artifacts")
        return None

    # -- default builders ------------------------------------------------------

    def _default_progress(self) -> dict[str, Any]:
        ids = self._index.ids()
        lessons = {
            lesson_id: {
                "status": "not-started",
                "startedAt": None,
                "submittedAt": None,
                "completedAt": None,
            }
            for lesson_id in ids
        }
        return {
            "version": 1,
            "currentLesson": ids[0] if ids else None,
            "updatedAt": None,
            "lessons": lessons,
        }

    def _default_answers(self, lesson_id: str) -> dict[str, Any]:
        return {
            "version": 1,
            "lesson": lesson_id,
            "mode": self._index.mode_for(lesson_id) or "concept",
            "status": "not-started",
            "updatedAt": None,
            "submittedAt": None,
            "answers": {},
            "artifacts": None,
        }
