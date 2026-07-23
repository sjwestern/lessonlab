from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from lessonlab.http_app import make_handler_class
from lessonlab.lessons import LessonIndex
from lessonlab.paths import Paths
from lessonlab.service import LessonService
from lessonlab.state import StateStore


@pytest.fixture()
def running_server(content_root: Path, paths: Paths):
    index = LessonIndex(paths.lessons_dir)
    store = StateStore(paths)
    service = LessonService(store, index)
    handler_class = make_handler_class(service, paths)

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    base_url = f"http://{host}:{port}"
    try:
        yield base_url, paths
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _get(url: str) -> tuple[int, dict]:
    with urllib.request.urlopen(url) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _request_json(url: str, method: str, body: dict) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def _get_raw(url: str) -> tuple[int, bytes, str]:
    with urllib.request.urlopen(url) as response:
        return (
            response.status,
            response.read(),
            response.headers.get("Content-Type", ""),
        )


class TestProgressRoute:
    def test_returns_defaults(self, running_server) -> None:
        base_url, _ = running_server
        status, body = _get(f"{base_url}/api/progress")
        assert status == 200
        assert body["currentLesson"] == "0001"
        assert set(body["lessons"].keys()) == {"0001", "0002"}


class TestAnswersRoute:
    def test_get_defaults(self, running_server) -> None:
        base_url, _ = running_server
        status, body = _get(f"{base_url}/api/lessons/0001/answers")
        assert status == 200
        assert body["status"] == "not-started"

    def test_get_unknown_lesson_404(self, running_server) -> None:
        base_url, _ = running_server
        request = urllib.request.Request(f"{base_url}/api/lessons/9999/answers")
        try:
            with urllib.request.urlopen(request):
                pytest.fail("expected 404")
        except urllib.error.HTTPError as error:
            assert error.code == 404
            body = json.loads(error.read().decode("utf-8"))
            assert "unknown lesson" in body["error"]

    def test_put_saves_draft(self, running_server) -> None:
        base_url, paths = running_server
        status, body = _request_json(
            f"{base_url}/api/lessons/0001/answers",
            "PUT",
            {"answers": {"q1": "draft"}},
        )
        assert status == 200
        assert body["status"] == "in-progress"
        # File is written where the paths object expects it.
        on_disk = json.loads(paths.answer_file("0001").read_text(encoding="utf-8"))
        assert on_disk["answers"] == {"q1": "draft"}

    def test_put_rejects_invalid_answer(self, running_server) -> None:
        base_url, _ = running_server
        status, body = _request_json(
            f"{base_url}/api/lessons/0001/answers",
            "PUT",
            {"answers": {"Bad-ID": "x"}},
        )
        assert status == 400
        assert "invalid response ID" in body["error"]


class TestSubmitRoute:
    def test_submit_concept(self, running_server) -> None:
        base_url, _ = running_server
        status, body = _request_json(
            f"{base_url}/api/lessons/0001/submit",
            "POST",
            {"answers": {"q1": "final"}},
        )
        assert status == 200
        assert body["status"] == "submitted"

    def test_submit_build_requires_artifacts(self, running_server) -> None:
        base_url, _ = running_server
        status, body = _request_json(
            f"{base_url}/api/lessons/0002/submit",
            "POST",
            {"answers": {"q1": "final"}},
        )
        assert status == 400
        assert "artifacts" in body["error"]

    def test_submit_build_with_artifacts(self, running_server) -> None:
        base_url, _ = running_server
        status, body = _request_json(
            f"{base_url}/api/lessons/0002/submit",
            "POST",
            {
                "answers": {"q1": "final"},
                "artifacts": {
                    "commitRef": "abcdef1",
                    "testNames": ["t"],
                    "artifactPaths": [],
                },
            },
        )
        assert status == 200
        assert body["artifacts"]["commitRef"] == "abcdef1"


class TestFrameworkAssets:
    def test_serves_framework_asset(self, running_server) -> None:
        base_url, paths = running_server
        # Ensure a real asset exists in the fixture framework root.
        # The default framework root is the real ``lessonlab/`` folder shipped
        # with this repo, which contains ``assets/course.css`` and ``quiz.js``.
        status, body, content_type = _get_raw(
            f"{base_url}/_framework/assets/course.css"
        )
        assert status == 200
        assert len(body) > 0
        assert content_type.startswith("text/css")

    def test_framework_asset_traversal_rejected(self, running_server) -> None:
        base_url, _ = running_server
        request = urllib.request.Request(
            f"{base_url}/_framework/assets/../schemas/answer.schema.json"
        )
        try:
            with urllib.request.urlopen(request) as response:
                # If urllib normalises the URL and the server serves it, the
                # request must at minimum not leak the schema through the
                # framework-assets endpoint.
                assert response.status != 200 or b"$schema" not in response.read()
        except urllib.error.HTTPError as error:
            assert error.code in (400, 404)


class TestApiFallback:
    def test_unknown_api_route_404(self, running_server) -> None:
        base_url, _ = running_server
        request = urllib.request.Request(f"{base_url}/api/nope")
        try:
            with urllib.request.urlopen(request):
                pytest.fail("expected 404")
        except urllib.error.HTTPError as error:
            assert error.code == 404
            payload = json.loads(error.read().decode("utf-8"))
            assert payload["error"] == "unknown API route"
