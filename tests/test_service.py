from __future__ import annotations

import pytest

from lessonlab.service import LessonNotFoundError, LessonService
from lessonlab.validation import ValidationError


class TestGetProgress:
    def test_default_progress_lists_all_lessons(self, service: LessonService) -> None:
        progress = service.get_progress()
        assert progress["version"] == 1
        assert progress["currentLesson"] == "0001"
        assert set(progress["lessons"].keys()) == {"0001", "0002"}
        assert all(entry["status"] == "not-started" for entry in progress["lessons"].values())


class TestGetAnswers:
    def test_returns_defaults_for_new_lesson(self, service: LessonService) -> None:
        state = service.get_answers("0001")
        assert state["lesson"] == "0001"
        assert state["mode"] == "concept"
        assert state["status"] == "not-started"
        assert state["answers"] == {}
        assert state["artifacts"] is None

    def test_unknown_lesson_raises(self, service: LessonService) -> None:
        with pytest.raises(LessonNotFoundError):
            service.get_answers("9999")


class TestSaveDraft:
    def test_concept_draft_updates_status_and_progress(self, service: LessonService) -> None:
        state = service.save_draft("0001", {"q1": "answer"}, None)

        assert state["status"] == "in-progress"
        assert state["submittedAt"] is None
        assert state["answers"] == {"q1": "answer"}
        assert state["artifacts"] is None

        progress = service.get_progress()
        assert progress["currentLesson"] == "0001"
        assert progress["lessons"]["0001"]["status"] == "in-progress"
        assert progress["lessons"]["0001"]["startedAt"] is not None
        assert progress["lessons"]["0001"]["submittedAt"] is None

    def test_concept_draft_rejects_artifacts(self, service: LessonService) -> None:
        with pytest.raises(ValidationError):
            service.save_draft("0001", {}, {"commitRef": "abcdef1"})

    def test_build_draft_without_artifacts_allowed(self, service: LessonService) -> None:
        state = service.save_draft("0002", {"q1": "draft"}, None)
        assert state["mode"] == "build"
        assert state["status"] == "in-progress"
        assert state["artifacts"] is None

    def test_build_draft_with_artifacts_validates(self, service: LessonService) -> None:
        state = service.save_draft(
            "0002",
            {"q1": "draft"},
            {"commitRef": "abcdef1", "testNames": ["t"], "artifactPaths": []},
        )
        assert state["artifacts"]["commitRef"] == "abcdef1"


class TestSubmit:
    def test_concept_submit_flips_status_and_stamps_submitted_at(self, service: LessonService) -> None:
        state = service.submit("0001", {"q1": "final"}, None)
        assert state["status"] == "submitted"
        assert state["submittedAt"] is not None

        progress = service.get_progress()
        assert progress["lessons"]["0001"]["status"] == "submitted"
        assert progress["lessons"]["0001"]["submittedAt"] == state["submittedAt"]

    def test_build_submit_requires_artifacts(self, service: LessonService) -> None:
        with pytest.raises(ValidationError):
            service.submit("0002", {"q1": "final"}, None)

    def test_build_submit_with_artifacts_succeeds(self, service: LessonService) -> None:
        state = service.submit(
            "0002",
            {"q1": "final"},
            {"commitRef": "1234567", "testNames": ["t"], "artifactPaths": ["src/x.py"]},
        )
        assert state["status"] == "submitted"
        assert state["artifacts"]["commitRef"] == "1234567"

    def test_concept_submit_rejects_artifacts(self, service: LessonService) -> None:
        with pytest.raises(ValidationError):
            service.submit("0001", {"q1": "final"}, {"commitRef": "abcdef1"})

    def test_unknown_lesson_raises(self, service: LessonService) -> None:
        with pytest.raises(LessonNotFoundError):
            service.submit("9999", {}, None)


class TestStartedAtPreserved:
    def test_started_at_does_not_change_on_second_write(self, service: LessonService) -> None:
        first = service.save_draft("0001", {"q1": "a"}, None)
        started = service.get_progress()["lessons"]["0001"]["startedAt"]
        assert started == first["updatedAt"]

        service.save_draft("0001", {"q1": "b"}, None)
        assert service.get_progress()["lessons"]["0001"]["startedAt"] == started
