# lessonlab

Local lesson runtime. Serves static HTML lessons and a tiny REST API that a browser
uses to save draft answers and submit them. Designed to be reused across courses.

Runtime has **zero third-party dependencies**. Only the test suite depends on
`pytest`.

## Layout

```
lessonlab/
  src/lessonlab/          # framework package (importable)
    paths.py              # where lessons, state, and framework assets live
    lessons.py            # lesson-file discovery + filename convention
    validation.py         # answer + artifact schema rules (single source of truth)
    state.py              # atomic JSON read/write for progress + answer files
    service.py            # use-case layer: get_progress, save_draft, submit
    http_app.py           # HTTP handler + route table
    cli.py                # lesson-server argparse + server bootstrap
    lessonlab_cli.py      # top-level lessonlab CLI (scaffold commands)
    scaffold.py           # lesson file scaffold helpers + template
  assets/                 # framework CSS/JS served at /_framework/assets/*
  schemas/                # JSON Schema (draft 2020-12) for answer files
  tests/                  # pytest suite
```

## Use from a course repository

The course repository provides the **content root**: `lessons/`, `reference/`,
`learning-state/`. Point the server at that root:

```bash
lesson-server --content-root /path/to/course
```

If invoked from the course repo without `--content-root`, the current working
directory is used.

Lesson HTML must reference framework assets by absolute URL:

```html
<link rel="stylesheet" href="/_framework/assets/course.css">
<script src="/_framework/assets/quiz.js" defer></script>
```

## Develop

```bash
cd lessonlab
uv sync
uv run pytest
```

## Run

From the course repo root:

```bash
uv run --project lessonlab lessonlab serve -- --content-root /path/to/course
```

Back-compat scripts still work:

```bash
uv run --project lessonlab lesson-server --content-root /path/to/course
uv run --project lessonlab lessonlab-validate --content-root /path/to/course
```

## Scaffold a lesson

Create a concept lesson with the next numeric id:

```bash
uv run --project lessonlab lessonlab scaffold lesson --slug intro-state-machines
```

Create a build lesson with custom title and response ids:

```bash
uv run --project lessonlab lessonlab scaffold lesson \
  --slug ship-artifacts \
  --mode build \
  --title "Ship artifacts" \
  --response-id design-notes \
  --response-id review-summary
```

This writes `lessons/NNNN-slug.(concept|build).html` under the content root
(default: current directory).

## Validate answer files

```bash
uv run --project lessonlab lessonlab validate -- --content-root /path/to/course
```
