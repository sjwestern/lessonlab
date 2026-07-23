from __future__ import annotations

import json
from pathlib import Path

from lessonlab.paths import Paths
from lessonlab.state import StateStore, read_json, write_json_atomic


def test_read_json_returns_default_when_missing(tmp_path: Path) -> None:
    assert read_json(tmp_path / "missing.json", {"x": 1}) == {"x": 1}


def test_write_json_atomic_creates_parent_and_no_temp_leak(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "file.json"
    write_json_atomic(target, {"a": 1, "b": [1, 2]})

    assert json.loads(target.read_text(encoding="utf-8")) == {"a": 1, "b": [1, 2]}
    # The temp file used during atomic replace must not remain.
    assert not (target.parent / "file.json.tmp").exists()


def test_write_json_atomic_is_sorted_and_indented(tmp_path: Path) -> None:
    target = tmp_path / "out.json"
    write_json_atomic(target, {"b": 2, "a": 1})
    content = target.read_text(encoding="utf-8")

    assert content.endswith("\n")
    assert content.index('"a"') < content.index('"b"')  # sort_keys=True


def test_state_store_roundtrip(tmp_path: Path) -> None:
    paths = Paths(content_root=tmp_path)
    store = StateStore(paths)

    store.write_progress({"version": 1, "hello": "world"})
    assert store.read_progress(None) == {"version": 1, "hello": "world"}

    store.write_answers("0001", {"lesson": "0001"})
    assert store.read_answers("0001", None) == {"lesson": "0001"}
