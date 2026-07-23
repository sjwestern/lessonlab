"""Answer and artifact validation.

This is the **single source of truth** for the rules encoded in
``schemas/answer.schema.json``. Both the HTTP write path and the offline
``lessonlab validate`` command import from here so the rules cannot drift.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Any


COMMIT_REF_RE = re.compile(r"^[a-f0-9]{7,40}$")
RESPONSE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
LESSON_ID_RE = re.compile(r"^[0-9]{4}$")

MAX_ANSWERS = 100
MAX_ANSWER_LENGTH = 10_000
MAX_ARTIFACT_LIST = 100
MAX_TEST_NAME_LENGTH = 200
MAX_ARTIFACT_PATH_LENGTH = 500


class ValidationError(ValueError):
    """Raised when submitted data violates the answer schema.

    Inherits from :class:`ValueError` so existing ``except ValueError`` guards
    keep working, but callers that want a schema-specific catch can use this
    type directly.
    """


def validate_answers(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or len(value) > MAX_ANSWERS:
        raise ValidationError(
            f"answers must be an object with at most {MAX_ANSWERS} entries"
        )
    validated: dict[str, str] = {}
    for response_id, answer in value.items():
        if not isinstance(response_id, str) or not RESPONSE_ID_RE.fullmatch(response_id):
            raise ValidationError(f"invalid response ID: {response_id!r}")
        if not isinstance(answer, str) or len(answer) > MAX_ANSWER_LENGTH:
            raise ValidationError(
                f"answer for {response_id!r} must be a string of at most "
                f"{MAX_ANSWER_LENGTH} characters"
            )
        validated[response_id] = answer
    return validated


def _valid_artifact_path(value: Any) -> bool:
    if not isinstance(value, str) or not (0 < len(value) <= MAX_ARTIFACT_PATH_LENGTH):
        return False
    if value.startswith("/"):
        return False
    parts = pathlib.PurePosixPath(value).parts
    return ".." not in parts and "" not in parts


def validate_artifacts(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError("artifacts must be an object")
    expected_keys = {"commitRef", "testNames", "artifactPaths"}
    extra = set(value.keys()) - expected_keys
    if extra:
        raise ValidationError(
            "artifacts may only contain commitRef, testNames, and artifactPaths; "
            f"unexpected keys: {sorted(extra)}"
        )
    for key in expected_keys:
        if key not in value:
            raise ValidationError(f"artifacts.{key} is required")

    commit_ref = value["commitRef"]
    if not isinstance(commit_ref, str) or not COMMIT_REF_RE.fullmatch(commit_ref):
        raise ValidationError(
            "artifacts.commitRef must be a git hash of 7 to 40 hex characters"
        )

    test_names = value["testNames"]
    if not isinstance(test_names, list) or len(test_names) > MAX_ARTIFACT_LIST:
        raise ValidationError(
            f"artifacts.testNames must be a list of at most {MAX_ARTIFACT_LIST} entries"
        )
    for name in test_names:
        if not isinstance(name, str) or not (0 < len(name) <= MAX_TEST_NAME_LENGTH):
            raise ValidationError(
                "each artifacts.testNames entry must be a non-empty string of at "
                f"most {MAX_TEST_NAME_LENGTH} characters"
            )

    artifact_paths = value["artifactPaths"]
    if not isinstance(artifact_paths, list) or len(artifact_paths) > MAX_ARTIFACT_LIST:
        raise ValidationError(
            f"artifacts.artifactPaths must be a list of at most {MAX_ARTIFACT_LIST} entries"
        )
    for path in artifact_paths:
        if not _valid_artifact_path(path):
            raise ValidationError(
                "each artifacts.artifactPaths entry must be a workspace-relative path"
            )

    if len(test_names) + len(artifact_paths) == 0:
        raise ValidationError(
            "artifacts must include at least one test name or artifact path"
        )

    return {
        "commitRef": commit_ref,
        "testNames": list(test_names),
        "artifactPaths": list(artifact_paths),
    }


# --- Offline validator (used by the ``lessonlab validate`` command) ---

REQUIRED_ANSWER_FILE_KEYS = {"version", "lesson", "mode", "status", "answers"}
ALLOWED_STATUSES = ("not-started", "in-progress", "submitted")


def validate_answer_file(path: pathlib.Path, expected_mode: str | None) -> list[str]:
    """Validate one answer file against the schema.

    Returns a list of human-readable problems (empty if valid). ``expected_mode``
    is the mode declared by the matching lesson filename, or ``None`` if the
    lesson is unknown.
    """

    prefix = f"[{path.name}]"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{prefix} could not read JSON: {error}"]

    problems: list[str] = []

    missing = REQUIRED_ANSWER_FILE_KEYS - data.keys()
    if missing:
        problems.append(f"{prefix} missing required keys: {sorted(missing)}")

    if data.get("version") != 1:
        problems.append(f"{prefix} version must be 1, got {data.get('version')!r}")

    lesson = data.get("lesson")
    if not isinstance(lesson, str) or not LESSON_ID_RE.fullmatch(lesson):
        problems.append(f"{prefix} lesson must be a 4-digit id, got {lesson!r}")
    elif path.stem != lesson:
        problems.append(
            f"{prefix} lesson id {lesson!r} does not match filename {path.stem!r}"
        )

    mode = data.get("mode")
    if mode not in ("concept", "build"):
        problems.append(f"{prefix} mode must be 'concept' or 'build', got {mode!r}")
    elif expected_mode is not None and expected_mode != mode:
        problems.append(
            f"{prefix} mode {mode!r} does not match lesson file mode {expected_mode!r}"
        )

    status = data.get("status")
    if status not in ALLOWED_STATUSES:
        problems.append(f"{prefix} status is invalid: {status!r}")

    try:
        validate_answers(data.get("answers"))
    except ValidationError as error:
        problems.append(f"{prefix} {error}")

    artifacts = data.get("artifacts")
    if mode == "build":
        if status == "submitted" and artifacts is None:
            problems.append(f"{prefix} submitted build lesson must include artifacts")
        elif artifacts is not None:
            try:
                validate_artifacts(artifacts)
            except ValidationError as error:
                problems.append(f"{prefix} {error}")
    elif mode == "concept" and artifacts is not None:
        problems.append(f"{prefix} concept lessons must not include artifacts")

    return problems


def validate_state_dir(
    answers_dir: pathlib.Path,
    lesson_modes: dict[str, str],
) -> list[str]:
    """Validate every answer file under ``answers_dir``."""

    problems: list[str] = []
    if not answers_dir.exists():
        return problems
    for path in sorted(answers_dir.glob("[0-9][0-9][0-9][0-9].json")):
        expected_mode = lesson_modes.get(path.stem)
        problems.extend(validate_answer_file(path, expected_mode))
    return problems


def main(argv: list[str] | None = None) -> int:
    """Validator entrypoint for ``lessonlab validate``.

    Discovers the content root the same way the server does (defaults to
    ``$PWD``) and validates every answer file in it.
    """

    import argparse

    from .lessons import LessonIndex
    from .paths import Paths

    parser = argparse.ArgumentParser(
        prog="lessonlab validate",
        description="Validate learning-state answer files against the answer schema.",
    )
    parser.add_argument(
        "--content-root",
        default=None,
        help="course repository root (default: current working directory)",
    )
    args = parser.parse_args(argv)

    content_root = pathlib.Path(args.content_root or ".").resolve()
    paths = Paths(content_root=content_root)
    index = LessonIndex(paths.lessons_dir)
    modes = {lesson_id: index.mode_for(lesson_id) or "" for lesson_id in index.ids()}

    problems = validate_state_dir(paths.answers_dir, modes)
    for problem in problems:
        print(problem, file=sys.stderr)

    if problems:
        print(f"validation failed: {len(problems)} problem(s)", file=sys.stderr)
        return 1

    print("all answer files valid")
    return 0
