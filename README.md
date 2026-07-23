# lessonlab

Local lesson runtime. Serves static HTML lessons and a tiny REST API that a browser
uses to save draft answers and submit them. Designed to be reused across courses.

Runtime has **zero third-party dependencies**. Only the test suite depends on
`pytest`.

## Install

### Install CLI

Install from GitHub:

```bash
uv tool install git+https://github.com/sjwestern/lessonlab.git
```

Upgrade later:

```bash
uv tool upgrade lessonlab
```

### Install `lessonlab-teach` skill

This repo ships the skill at:

- `.agents/skills/lessonlab-teach`

Install with `npx skills`:

```bash
npx skills install github:sjwestern/lessonlab/.agents/skills/lessonlab-teach#v0.1.0
```

If your `skills` CLI uses a different GitHub target format, keep the same rule:
install from this repo and pin the same tag as the CLI.

## Versioning policy - CLI + skill

Use one tag for both `lessonlab` CLI and `lessonlab-teach` skill.

Example:

```bash
uv tool install git+https://github.com/sjwestern/lessonlab.git@v0.1.0
npx skills install github:sjwestern/lessonlab/.agents/skills/lessonlab-teach#v0.1.0
```

Do not install from floating `main` for shared or production course repos.

## Use in a course repo

The course repo is the **content root**. It should contain:

- `lessons/`
- `reference/`
- `learning-state/`

### Initialize course layout

From the course repo root:

```bash
lessonlab init
```

Or target another path:

```bash
lessonlab init --content-root /path/to/course
```

This creates `lessons/`, `reference/`, `learning-state/answers/`, and
`learning-state/progress.json`.

### Generate lessons with `lessonlab-teach`

Use the `lessonlab-teach` skill to draft lesson content. The agent should run
`lessonlab scaffold lesson` itself, then fill the generated file.

Suggested flow:

1. Ask your agent to use `lessonlab-teach` and create a lesson for your topic.
2. The agent scaffolds with `lessonlab scaffold lesson ...` and writes content.
3. The agent runs validation:

```bash
lessonlab validate --content-root .
```

4. The agent fixes any reported issues and re-runs validation until clean.

The skill owns teaching guidance. The CLI owns file naming, schema rules, and
runtime behavior.

### Serve lessons

```bash
lessonlab serve --content-root /path/to/course
```

If `--content-root` is omitted, current working directory is used.

Lesson HTML must use absolute framework asset URLs:

```html
<link rel="stylesheet" href="/_framework/assets/course.css">
<script src="/_framework/assets/quiz.js" defer></script>
```

### Scaffold lessons

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

This writes `lessons/NNNN-slug.(concept|build).html`.

### Validate answer files

```bash
lessonlab validate --content-root /path/to/course
```

## Development

### Editable CLI install

Clone and install as editable tool:

```bash
git clone https://github.com/sjwestern/lessonlab.git ~/projects/sjwestern/lessonlab
uv tool install --editable ~/projects/sjwestern/lessonlab
```

Local code changes are picked up without reinstalling.

### Skill dev workflow (live updates)

Symlink the skill into a course repo:

```bash
mkdir -p /path/to/course/.agents/skills
ln -sfn ~/projects/sjwestern/lessonlab/.agents/skills/lessonlab-teach \
  /path/to/course/.agents/skills/lessonlab-teach
```

This is the skill equivalent of editable install.

### Run tests

```bash
cd lessonlab
uv sync
uv run python -m pytest
```

## Repo layout

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
    commands/             # command modules (serve, validate, scaffold, init)
    scaffold.py           # lesson file scaffold helpers + template
  assets/                 # framework CSS/JS served at /_framework/assets/*
  schemas/                # JSON Schema (draft 2020-12) for answer files
  tests/                  # pytest suite
```
