"""HTTP transport layer.

A small route table dispatches ``(method, path)`` to functions that speak to
:class:`~lessonlab.service.LessonService`. Static files are served from two
roots:

- ``/_framework/assets/*`` -> the framework's packaged assets.
- everything else -> the course's content root (lessons, reference, ...).
"""

from __future__ import annotations

import http.server
import json
import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .paths import Paths
from .service import LessonNotFoundError, LessonService
from .validation import ValidationError


MAX_BODY_BYTES = 64 * 1024
FRAMEWORK_ASSETS_PREFIX = "/_framework/assets/"


# -- route table --------------------------------------------------------------

Handler = Callable[["LessonRequestHandler", re.Match[str]], None]


@dataclass(frozen=True)
class Route:
    method: str
    pattern: re.Pattern[str]
    handler: Handler


def _route(method: str, pattern: str, handler: Handler) -> Route:
    return Route(method=method, pattern=re.compile(pattern), handler=handler)


def _handle_get_progress(handler: "LessonRequestHandler", _match: re.Match[str]) -> None:
    handler.send_json(200, handler.service.get_progress())


def _handle_get_answers(handler: "LessonRequestHandler", match: re.Match[str]) -> None:
    try:
        answers = handler.service.get_answers(match.group("id"))
    except LessonNotFoundError as error:
        handler.send_api_error(404, str(error))
        return
    handler.send_json(200, answers)


def _handle_put_answers(handler: "LessonRequestHandler", match: re.Match[str]) -> None:
    _handle_write(handler, match, submit=False)


def _handle_submit(handler: "LessonRequestHandler", match: re.Match[str]) -> None:
    _handle_write(handler, match, submit=True)


def _handle_write(
    handler: "LessonRequestHandler",
    match: re.Match[str],
    *,
    submit: bool,
) -> None:
    lesson_id = match.group("id")
    try:
        payload = handler.read_request_json()
        answers_payload = payload.get("answers") if isinstance(payload, dict) else None
        artifacts_payload = payload.get("artifacts") if isinstance(payload, dict) else None
        if submit:
            state = handler.service.submit(lesson_id, answers_payload, artifacts_payload)
        else:
            state = handler.service.save_draft(lesson_id, answers_payload, artifacts_payload)
    except LessonNotFoundError as error:
        handler.send_api_error(404, str(error))
        return
    except (ValidationError, ValueError, AttributeError, TypeError) as error:
        handler.send_api_error(400, str(error))
        return
    handler.send_json(200, state)


ROUTES: tuple[Route, ...] = (
    _route("GET",  r"^/api/progress$",                                _handle_get_progress),
    _route("GET",  r"^/api/lessons/(?P<id>[0-9]{4})/answers$",        _handle_get_answers),
    _route("PUT",  r"^/api/lessons/(?P<id>[0-9]{4})/answers$",        _handle_put_answers),
    _route("POST", r"^/api/lessons/(?P<id>[0-9]{4})/submit$",         _handle_submit),
)


# -- handler ------------------------------------------------------------------

class LessonRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Serves the course content root and dispatches ``/api/*`` to the service."""

    # These are populated by :func:`make_handler_class`.
    service: LessonService
    paths: Paths

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # ``directory`` is set from the injected ``paths.content_root`` so that
        # ``SimpleHTTPRequestHandler`` serves lessons, reference, and state
        # from the course repository.
        super().__init__(*args, directory=str(self.paths.content_root), **kwargs)

    # --- JSON helpers -----------------------------------------------------

    def send_json(self, status: int, value: Any) -> None:
        encoded = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def send_api_error(self, status: int, message: str) -> None:
        self.send_json(status, {"error": message})

    def read_request_json(self) -> Any:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("invalid Content-Length") from error
        if content_length <= 0 or content_length > MAX_BODY_BYTES:
            raise ValueError(f"request body must be 1-{MAX_BODY_BYTES} bytes")
        try:
            return json.loads(self.rfile.read(content_length))
        except json.JSONDecodeError as error:
            raise ValueError("request body must be valid JSON") from error

    # --- routing ---------------------------------------------------------

    def _dispatch_api(self) -> bool:
        path = urllib.parse.urlsplit(self.path).path
        for route in ROUTES:
            if route.method != self.command:
                continue
            match = route.pattern.fullmatch(path)
            if match:
                route.handler(self, match)
                return True
        if path.startswith("/api/"):
            self.send_api_error(404, "unknown API route")
            return True
        return False

    def _serve_framework_asset(self) -> bool:
        path = urllib.parse.urlsplit(self.path).path
        if not path.startswith(FRAMEWORK_ASSETS_PREFIX):
            return False
        relative = path[len(FRAMEWORK_ASSETS_PREFIX):]
        # Guard against traversal; SimpleHTTPRequestHandler normally does this
        # for its own directory but we're serving from a separate root here.
        relative_parts = Path(relative).parts
        if ".." in relative_parts or relative.startswith("/"):
            self.send_error(404, "not found")
            return True
        asset_path = self.paths.framework_assets_dir / relative
        if not asset_path.is_file():
            self.send_error(404, "not found")
            return True
        try:
            data = asset_path.read_bytes()
        except OSError:
            self.send_error(404, "not found")
            return True
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(str(asset_path)))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)
        return True

    # --- SimpleHTTPRequestHandler hooks -----------------------------------

    def do_GET(self) -> None:  # noqa: N802 - required signature
        if self._serve_framework_asset():
            return
        if self._dispatch_api():
            return
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        if self.path.startswith(FRAMEWORK_ASSETS_PREFIX):
            # Fall back to full GET for framework assets; volume is tiny.
            self._serve_framework_asset()
            return
        super().do_HEAD()

    def do_PUT(self) -> None:  # noqa: N802
        if self._dispatch_api():
            return
        self.send_api_error(404, "unknown API route")

    def do_POST(self) -> None:  # noqa: N802
        if self._dispatch_api():
            return
        self.send_api_error(404, "unknown API route")


def make_handler_class(service: LessonService, paths: Paths) -> type[LessonRequestHandler]:
    """Return a handler class bound to a specific service and paths.

    ``http.server.ThreadingHTTPServer`` instantiates the handler per request
    with a fixed signature, so we bake the dependencies onto a subclass here.
    """

    return type(
        "BoundLessonRequestHandler",
        (LessonRequestHandler,),
        {"service": service, "paths": paths},
    )
