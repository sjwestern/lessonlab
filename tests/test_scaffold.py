from __future__ import annotations

from pathlib import Path

from lessonlab import cli


def test_scaffold_creates_next_concept_lesson(tmp_path: Path) -> None:
    lessons_dir = tmp_path / "lessons"
    lessons_dir.mkdir()
    (lessons_dir / "0002-already-here.concept.html").write_text("x", encoding="utf-8")

    exit_code = cli.main(
        [
            "scaffold",
            "lesson",
            "--content-root",
            str(tmp_path),
            "--slug",
            "new-topic",
        ]
    )

    assert exit_code == 0
    created = lessons_dir / "0003-new-topic.concept.html"
    assert created.exists()
    content = created.read_text(encoding="utf-8")
    assert 'data-lesson-id="0003"' in content
    assert 'data-response-id="response-1"' in content


def test_scaffold_fails_if_target_exists_without_force(tmp_path: Path) -> None:
    lessons_dir = tmp_path / "lessons"
    lessons_dir.mkdir()
    existing = lessons_dir / "0001-topic.concept.html"
    existing.write_text("old", encoding="utf-8")

    exit_code = cli.main(
        [
            "scaffold",
            "lesson",
            "--content-root",
            str(tmp_path),
            "--slug",
            "topic",
            "--id",
            "1",
        ]
    )

    assert exit_code == 1
    assert existing.read_text(encoding="utf-8") == "old"


def test_scaffold_creates_build_lesson_with_artifact_fields(tmp_path: Path) -> None:
    exit_code = cli.main(
        [
            "scaffold",
            "lesson",
            "--content-root",
            str(tmp_path),
            "--slug",
            "ship-it",
            "--mode",
            "build",
            "--id",
            "7",
        ]
    )

    assert exit_code == 0
    created = tmp_path / "lessons" / "0007-ship-it.build.html"
    content = created.read_text(encoding="utf-8")
    assert 'data-artifact-field="commitRef"' in content
    assert 'data-artifact-field="testNames"' in content
    assert 'data-artifact-field="artifactPaths"' in content


def test_scaffold_force_overwrites_existing_file(tmp_path: Path) -> None:
    lessons_dir = tmp_path / "lessons"
    lessons_dir.mkdir()
    existing = lessons_dir / "0001-topic.concept.html"
    existing.write_text("old", encoding="utf-8")

    exit_code = cli.main(
        [
            "scaffold",
            "lesson",
            "--content-root",
            str(tmp_path),
            "--slug",
            "topic",
            "--id",
            "1",
            "--force",
        ]
    )

    assert exit_code == 0
    assert "old" not in existing.read_text(encoding="utf-8")


def test_scaffold_uses_custom_title_and_response_ids(tmp_path: Path) -> None:
    exit_code = cli.main(
        [
            "scaffold",
            "lesson",
            "--content-root",
            str(tmp_path),
            "--slug",
            "topic",
            "--title",
            "Custom Title",
            "--response-id",
            "first-answer",
            "--response-id",
            "second-answer",
        ]
    )

    assert exit_code == 0
    created = tmp_path / "lessons" / "0001-topic.concept.html"
    content = created.read_text(encoding="utf-8")
    assert "<h1>Custom Title</h1>" in content
    assert 'data-response-id="first-answer"' in content
    assert 'data-response-id="second-answer"' in content


def test_scaffold_rejects_invalid_response_id(tmp_path: Path) -> None:
    exit_code = cli.main(
        [
            "scaffold",
            "lesson",
            "--content-root",
            str(tmp_path),
            "--slug",
            "topic",
            "--response-id",
            "Bad-ID",
        ]
    )

    assert exit_code == 1


def test_lessonlab_serve_dispatches_to_serve_runner(monkeypatch) -> None:
    seen: list[tuple[str, bool]] = []

    def fake_run_serve(args) -> int:
        seen.append((args.lesson, args.list))
        return 12

    monkeypatch.setattr(cli, "_run_serve", fake_run_serve)

    exit_code = cli.main(["serve", "--list", "--lesson", "0002"])

    assert exit_code == 12
    assert seen == [("0002", True)]


def test_lessonlab_validate_delegates_to_validate_cli(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_validate(argv: list[str] | None = None) -> int:
        calls.append(argv or [])
        return 3

    monkeypatch.setattr(cli, "validate_main", fake_validate)

    exit_code = cli.main(["validate", "--content-root", "/tmp/course"])

    assert exit_code == 3
    assert calls == [["--content-root", "/tmp/course"]]
