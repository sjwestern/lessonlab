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
    cli.py                # top-level lessonlab CLI entrypoint + dispatch
    commands/             # command modules (serve, validate, scaffold)
    scaffold.py           # lesson file scaffold helpers + template
  assets/                 # framework CSS/JS served at /_framework/assets/*
  schemas/                # JSON Schema (draft 2020-12) for answer files
  tests/                  # pytest suite
```

## Install for reuse across repositories

### Option 1 - install from git (regular use)

Install once, then use `lessonlab` from any repo:

```bash
uv tool install git+https://github.com/sjwestern/lessonlab.git
```

Use from a course repo:

```bash
cd /path/to/course
lessonlab serve --content-root .
```

Upgrade later:

```bash
uv tool upgrade lessonlab
```

### Option 2 - clone + editable tool install (active development)

Clone locally and install as an editable tool:

```bash
git clone https://github.com/sjwestern/lessonlab.git ~/projects/sjwestern/lessonlab
uv tool install --editable ~/projects/sjwestern/lessonlab
```

Use from a course repo:

```bash
cd /path/to/course
lessonlab serve --content-root .
```

Editable install means local code changes in `~/projects/sjwestern/lessonlab` are picked up
without reinstalling.

## Use from a course repository

The course repository provides the **content root**: `lessons/`, `reference/`,
`learning-state/`. Point the server at that root:

```bash
lessonlab serve --content-root /path/to/course
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
lessonlab serve --content-root /path/to/course
```

## Scaffold a lesson

Create a concept lesson with the next numeric id:

```bash
lessonlab scaffold lesson --slug intro-state-machines
```

Create a build lesson with custom title and response ids:

```bash
lessonlab scaffold lesson \
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
lessonlab validate --content-root /path/to/course
```
