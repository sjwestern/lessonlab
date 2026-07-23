from __future__ import annotations

import json
from pathlib import Path

from lessonlab import cli


def test_init_creates_learn_repo_layout(tmp_path: Path) -> None:
    exit_code = cli.main(["init", "--content-root", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "lessons").is_dir()
    assert (tmp_path / "reference").is_dir()
    assert (tmp_path / "learning-state" / "answers").is_dir()

    progress = json.loads(
        (tmp_path / "learning-state" / "progress.json").read_text(encoding="utf-8")
    )
    assert progress == {
        "version": 1,
        "currentLesson": None,
        "updatedAt": None,
        "lessons": {},
    }


def test_init_fails_if_progress_exists_without_force(tmp_path: Path) -> None:
    progress_path = tmp_path / "learning-state" / "progress.json"
    progress_path.parent.mkdir(parents=True)
    progress_path.write_text('{"version": 99}\n', encoding="utf-8")

    exit_code = cli.main(["init", "--content-root", str(tmp_path)])

    assert exit_code == 1
    assert json.loads(progress_path.read_text(encoding="utf-8")) == {"version": 99}


def test_init_force_overwrites_progress(tmp_path: Path) -> None:
    progress_path = tmp_path / "learning-state" / "progress.json"
    progress_path.parent.mkdir(parents=True)
    progress_path.write_text('{"version": 99}\n', encoding="utf-8")

    exit_code = cli.main(["init", "--content-root", str(tmp_path), "--force"])

    assert exit_code == 0
    assert json.loads(progress_path.read_text(encoding="utf-8")) == {
        "version": 1,
        "currentLesson": None,
        "updatedAt": None,
        "lessons": {},
    }


def test_lessonlab_init_dispatches_to_init_runner(monkeypatch) -> None:
    seen: list[tuple[str | None, bool]] = []

    def fake_run_init(args) -> int:
        seen.append((args.content_root, args.force))
        return 17

    monkeypatch.setattr(cli, "_run_init", fake_run_init)

    exit_code = cli.main(["init", "--content-root", "/tmp/course", "--force"])

    assert exit_code == 17
    assert seen == [("/tmp/course", True)]
