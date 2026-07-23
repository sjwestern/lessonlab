from __future__ import annotations

import pytest

from lessonlab.validation import (
    ValidationError,
    validate_answers,
    validate_artifacts,
)


class TestValidateAnswers:
    def test_accepts_valid_map(self) -> None:
        assert validate_answers({"q-one": "a", "q2": ""}) == {"q-one": "a", "q2": ""}

    def test_rejects_non_dict(self) -> None:
        with pytest.raises(ValidationError):
            validate_answers([("q1", "a")])

    def test_rejects_bad_response_id(self) -> None:
        with pytest.raises(ValidationError):
            validate_answers({"BadID": "a"})

    def test_rejects_non_string_answer(self) -> None:
        with pytest.raises(ValidationError):
            validate_answers({"q1": 42})

    def test_enforces_max_length(self) -> None:
        with pytest.raises(ValidationError):
            validate_answers({"q1": "x" * 10_001})

    def test_enforces_max_entries(self) -> None:
        payload = {f"q{i}": "a" for i in range(101)}
        with pytest.raises(ValidationError):
            validate_answers(payload)


class TestValidateArtifacts:
    def _valid(self) -> dict[str, object]:
        return {
            "commitRef": "abcdef1",
            "testNames": ["test_thing"],
            "artifactPaths": ["src/foo.py"],
        }

    def test_accepts_valid_payload(self) -> None:
        assert validate_artifacts(self._valid()) == self._valid()

    def test_requires_all_keys(self) -> None:
        payload = self._valid()
        del payload["commitRef"]
        with pytest.raises(ValidationError):
            validate_artifacts(payload)

    def test_rejects_unknown_keys(self) -> None:
        payload = self._valid()
        payload["extra"] = "nope"
        with pytest.raises(ValidationError):
            validate_artifacts(payload)

    @pytest.mark.parametrize("commit", ["short", "GHIJKLM", "abcd123XYZ"])
    def test_rejects_bad_commit_ref(self, commit: str) -> None:
        payload = self._valid()
        payload["commitRef"] = commit
        with pytest.raises(ValidationError):
            validate_artifacts(payload)

    def test_requires_at_least_one_evidence_entry(self) -> None:
        payload = self._valid()
        payload["testNames"] = []
        payload["artifactPaths"] = []
        with pytest.raises(ValidationError):
            validate_artifacts(payload)

    @pytest.mark.parametrize(
        "bad_path",
        ["/absolute/no", "../escape", "nested/../escape", "", "x" * 501],
    )
    def test_rejects_bad_artifact_paths(self, bad_path: str) -> None:
        payload = self._valid()
        payload["artifactPaths"] = [bad_path]
        with pytest.raises(ValidationError):
            validate_artifacts(payload)

    def test_rejects_empty_test_name(self) -> None:
        payload = self._valid()
        payload["testNames"] = [""]
        with pytest.raises(ValidationError):
            validate_artifacts(payload)
