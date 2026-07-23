"""Lesson scaffolding helpers."""

from __future__ import annotations

import re
from pathlib import Path

from .lessons import LessonIndex
from .paths import Paths

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RESPONSE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
VALID_MODES = ("concept", "build")


def scaffold_lesson(
    *,
    paths: Paths,
    slug: str,
    mode: str,
    lesson_id: str | None,
    force: bool,
    title: str | None,
    response_ids: list[str] | None,
) -> Path:
    """Create one lesson file and return its path."""

    if not SLUG_RE.fullmatch(slug):
        raise ValueError("slug must match [a-z0-9][a-z0-9-]*")
    if mode not in VALID_MODES:
        raise ValueError("mode must be 'concept' or 'build'")

    resolved_title = title.strip() if title else slug.replace("-", " ").title()
    if not resolved_title:
        raise ValueError("title must not be empty")

    resolved_response_ids = response_ids or ["response-1"]
    for response_id in resolved_response_ids:
        if not RESPONSE_ID_RE.fullmatch(response_id):
            raise ValueError(
                f"response id must match [a-z0-9][a-z0-9-]{{0,63}}: {response_id!r}"
            )

    resolved_id = _resolve_lesson_id(paths.lessons_dir, lesson_id)
    filename = f"{resolved_id}-{slug}.{mode}.html"

    paths.lessons_dir.mkdir(parents=True, exist_ok=True)
    target = paths.lessons_dir / filename
    if target.exists() and not force:
        raise FileExistsError(f"lesson already exists: {target.name}")

    target.write_text(
        _lesson_html_template(
            lesson_id=resolved_id,
            title=resolved_title,
            mode=mode,
            response_ids=resolved_response_ids,
        ),
        encoding="utf-8",
    )
    return target


def _resolve_lesson_id(lessons_dir: Path, lesson_id: str | None) -> str:
    if lesson_id is not None:
        if not lesson_id.isdigit() or len(lesson_id) > 4:
            raise ValueError("id must be numeric and up to 4 digits")
        return lesson_id.zfill(4)

    index = LessonIndex(lessons_dir)
    ids = index.ids()
    if not ids:
        return "0001"
    return str(int(ids[-1]) + 1).zfill(4)


def _lesson_html_template(
    *,
    lesson_id: str,
    title: str,
    mode: str,
    response_ids: list[str],
) -> str:
    artifacts_block = ""
    if mode == "build":
        artifacts_block = """
    <section>
      <h2>Build artifacts</h2>
      <div class=\"response-field\">
        <label for=\"commit-ref\">Commit ref</label>
        <input id=\"commit-ref\" data-artifact-field=\"commitRef\" type=\"text\" />
      </div>
      <div class=\"response-field\">
        <label for=\"test-names\">Passing tests (one per line)</label>
        <textarea id=\"test-names\" data-artifact-field=\"testNames\"></textarea>
      </div>
      <div class=\"response-field\">
        <label for=\"artifact-paths\">Artifact paths (one per line)</label>
        <textarea id=\"artifact-paths\" data-artifact-field=\"artifactPaths\"></textarea>
      </div>
    </section>
"""

    response_sections = "\n".join(
        _response_field_html(response_id, index)
        for index, response_id in enumerate(response_ids, start=1)
    )

    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{lesson_id} {title}</title>
    <link rel=\"stylesheet\" href=\"/_framework/assets/course.css\" />
    <script src=\"/_framework/assets/quiz.js\" defer></script>
  </head>
  <body>
    <main data-lesson-id=\"{lesson_id}\">
      <header>
        <p class=\"kicker\">Lesson {lesson_id} - {mode}</p>
        <h1>{title}</h1>
      </header>

      <section>
        <h2>Prompt</h2>
        <p>Write lesson content here.</p>
      </section>

{response_sections}
{artifacts_block}
      <section class=\"lesson-state\">
        <p data-lesson-status>Lesson status: Not started</p>
        <p class=\"save-status\" data-save-status>Answers have not been saved yet.</p>
        <button type=\"button\" data-submit-lesson>Submit lesson</button>
        <p class=\"submit-status\" data-submit-status></p>
      </section>
    </main>
  </body>
</html>
"""


def _response_field_html(response_id: str, index: int) -> str:
    return f"""      <section class=\"response-field\">
        <label for=\"{response_id}\">Response {index}</label>
        <textarea
          id=\"{response_id}\"
          data-response-id=\"{response_id}\"
          required
        ></textarea>
      </section>"""
