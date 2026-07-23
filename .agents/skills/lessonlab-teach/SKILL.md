---
name: lessonlab-teach
description: Teach the user a new skill or concept in a LessonLab workspace.
disable-model-invocation: true
argument-hint: "What would you like to learn about?"
---

The user has asked you to teach them something. This is a stateful request - they intend to learn the topic over multiple sessions.

## Teaching Workspace

Treat the current directory as a teaching workspace. The state of their learning is captured in this directory in several files:

- `MISSION.md`: A document capturing the _reason_ the user is interested in the topic. This should be used to ground all teaching. Use the format in [MISSION-FORMAT.md](./MISSION-FORMAT.md).
- `./reference/*.html`: A directory of reference materials. These are the compressed learnings from the lessons - cheat sheets, reference algorithms, syntax, yoga poses, glossaries. They are the raw units of learning. They should be beautiful documents which print out well, and are designed for quick reference.
- `RESOURCES.md`: A list of resources which can be explored to ground your teaching in contextual knowledge, or to acquire knowledge and wisdom. Use the format in [RESOURCES-FORMAT.md](./RESOURCES-FORMAT.md).
- `./learning-records/*.md`: A directory of learning records, which capture what the user has learned. These are loosely equivalent to architectural decision records in software development - they capture non-obvious lessons and key insights that may need to be revised later, or drive future sessions. These should be used to calculate the zone of proximal development. They are titled `0001-<dash-case-name>.md`, where the number increments each time. Use the format in [LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md).
- `./lessons/*.html`: A directory of lessons. A **lesson** is a single, self-contained HTML output that teaches one tightly-scoped thing tied to the mission. This is the primary unit of teaching in this workspace. Lesson files must follow `NNNN-slug.concept.html` or `NNNN-slug.build.html` and should be created via `lessonlab scaffold lesson`.
- `./assets/*`: Reusable **components** shared across lessons. See [Assets](#assets).
- `NOTES.md`: A scratchpad for you to jot down user preferences, or working notes.

## LessonLab CLI workflow

Treat `lessonlab` CLI as the source of truth for repository structure and lesson file naming.

- Initialize workspace structure with `lessonlab init`.
- Create lessons with `lessonlab scaffold lesson ...`.
- Validate learner submissions with `lessonlab validate`.
- Preview and run lessons with `lessonlab serve`.

Do not manually invent lesson filenames. Use `lessonlab scaffold lesson` so files always match the required format.

## Lesson modes

Every generated lesson is in one of two modes. The mode is encoded in the filename and validated by LessonLab.

### Concept lessons (`NNNN-slug.concept.html`)

- Shape: worked example -> guided exercise -> independent exercise -> short written observation.
- Multiple-choice checks are allowed; interactive Check buttons give immediate feedback.
- Output: an answers file with prose or short-string responses.
- Done when: at least one independent exercise is completed without prompts, and the observation captures the general rule rather than only the specific case.
- Use for: introducing new vocabulary, protocol mechanics, or reasoning patterns where the learner has no schema yet.

### Build lessons (`NNNN-slug.build.html`)

- Shape: a task list with acceptance criteria; the learner produces committed evidence.
- No multiple-choice checks.
- Output: an answers file that also includes an `artifacts` object with a git commit reference, at least one test name, and at least one artifact path (ADR, trace-matrix row, runbook line, release note, or code path).
- Done when: code compiles/runs, at least one positive and one negative test pass, the artifact update is committed, and any referenced requirement ID is real.
- Use for: consolidating a concept into a skill, and for topics where usability, timing, concurrency, or OS behavior cannot be assessed by a quiz (Linux services, HMI usability, DDS QoS under churn, release control, traceability).

### Mode-selection rules for lesson generation

- Default rhythm: alternate concept and build lessons unless a rule below overrides.
- Force build when: the topic is Linux service behavior, HMI usability, release control, or traceability artifacts; or the learner's prior lesson shows they predicted answers before checking; or a capability in `LEARNING_PATH.md` has had two concept lessons without a build.
- Force concept when: the topic introduces new vocabulary (DDS QoS policies, DOORS terms, safety-standard names); or the learner's prior evidence shows guessing without reasoning; or no schema for the topic yet exists in prior lessons.

### Naming and validation

- Filenames must end with `.concept.html` or `.build.html`.
- Use `lessonlab scaffold lesson` to create lesson files with valid mode suffixes.
- Use `lessonlab validate --content-root .` to validate answer files.
- Build-lesson submissions must include a well-formed `artifacts` object; concept-lesson submissions must omit it.
- For install and CLI usage, follow this repository `README.md`.

## Lesson authoring rules

- When generating lessons, follow the mode rules in this skill under `Lesson modes`, including the required filename suffix (`.concept.html` or `.build.html`) and matching answer-file shape.
- When generating lessons, use worked examples and exercises to illustrate concepts.
- When using worked examples, use learner-facing language instead of pedagogy labels. Example phrasing: "Follow the diagnosis", "Choose the failed step", "Diagnose it yourself".
- Define jargon and technical terms in plain language when they are first introduced.
- Lesson and reference HTML must load framework CSS/JS via absolute URLs:
  - `href="/_framework/assets/course.css"`
  - `src="/_framework/assets/quiz.js"`
- Do not reference framework files via relative paths from content files. Serve framework assets through `lessonlab serve` at `/_framework/*`.

## Philosophy

To learn at a deep level, the user needs three things:

- **Knowledge**, captured from high-quality, high-trust resources
- **Skills**, acquired through highly-relevant interactive lessons devised by you, based on the knowledge
- **Wisdom**, which comes from interacting with other learners and practitioners

Before the `RESOURCES.md` is well-populated, your focus should be to find high-quality resources which will help the user acquire knowledge. Never trust your parametric knowledge.

Some topics may require more skills than knowledge. Learning more about theoretical physics might be more knowledge-based. For yoga, more skills-based.

### Fluency vs Storage Strength

You should be careful to split between two types of learning:

- **Fluency strength**: in-the-moment retrieval of knowledge
- **Storage strength**: long-term retention of knowledge

Fluency can give the user an illusory sense of mastery, but storage strength is the real goal. Try to design lessons which build long-term retention by desirable difficulty:

- Using retrieval practice (recall from memory)
- Spacing (distributing practice over time)
- Interleaving (mixing up different but related topics in practice - for skills practice only)

## Lessons

A lesson is the main thing you produce - the unit in which knowledge and skills reach the user. Each lesson is one self-contained HTML file, saved to `./lessons/` and titled `NNNN-slug.concept.html` or `NNNN-slug.build.html`.

Always create the file with LessonLab CLI, not by hand. Use:

- `lessonlab scaffold lesson --slug <dash-case-name> --mode concept`
- `lessonlab scaffold lesson --slug <dash-case-name> --mode build`

A lesson should be **beautiful** — clean, readable typography and layout — since the user will return to these later to review. Think Tufte.

The lesson should be short, and completable very quickly. Learners' working memory is very small, and we need to stay within it. But each lesson should give the user a single tangible win that they can build on. It should be directly tied to the mission, and should be in the user's zone of proximal development.

If possible, open the lesson file for the user by running a CLI command. Prefer serving lessons with `lessonlab serve --content-root .`.

Each lesson should link via HTML anchors to other lessons and reference documents.

Each lesson should recommend a primary source for the user to read or watch. This should be the most high-quality, high-trust resource you found on the topic.

Each lesson should contain a reminder to ask followup questions to the agent. The agent is their teacher, and can assist with anything that's unclear.

## Assets

Lessons are built from reusable **components**, stored in `./assets/`: stylesheets, quiz widgets, simulators, diagram helpers — anything a second lesson could reuse.

Reuse is the default, not the exception. Before authoring a lesson, read `./assets/` and build from the components already there. When a lesson needs something new and reusable, write it as a component in `./assets/` and link to it — never inline code a future lesson would duplicate.

A shared stylesheet is the first component every workspace earns: every lesson links it, so the lessons look like one consistent course rather than a pile of one-offs. As the workspace grows, so should the component library.

## The Mission

Every lesson should be tied into the mission - the reason that the user is interested in learning about the topic.

If the user is unclear about the mission, or the `MISSION.md` is not populated, your first job should be to question the user on why they want to learn this.

Failing to understand the mission will mean knowledge acquisition is not grounded in real-world goals. Lessons will feel too abstract. You will have no way of judging what the user should do next.

Missions may change as the user develops more skills and knowledge. This is normal - make sure to update the `MISSION.md` and add a learning record to capture the change. Confirm with the user before changing the mission.

## Zone Of Proximal Development

Each lesson, the user should always feel as if they are being challenged 'just enough'.

The user may specify an exact thing they want to learn. If they don't, figure out their zone of proximal development by:

- Reading their `learning-records`
- Figuring out the right thing to teach them based on their mission
- Teach the most relevant thing that fits in their zone of proximal development

## Knowledge

Lessons should be designed around a skill the user is going to learn. The knowledge in the lesson should be only what's required to acquire that skill. You teach the knowledge first, then get the user to practice the skills via an interactive feedback loop.

Knowledge should first be gathered from trusted resources. Use `RESOURCES.md` to keep track of them. Lessons should be littered with citations - links to external resources to back up any claim made. This increases the trustworthiness of the lesson.

For acquiring knowledge, difficulty is the enemy. It eats working memory you need for understanding.

## Skills

If knowledge is all about acquisition, skills are about durability and flexibility. Make the knowledge stick.

For skill acquisition, difficulty is the tool. Effortful retrieval is what builds storage strength. Skills should be taught through interactive lessons. There are several tools at your disposal:

- Interactive lessons, using quizzes and light in-browser tasks
- Lessons which guide the user through a list of real-world steps to take (for instance, yoga poses)

Each of these should be based on a **feedback loop**, where the user receives feedback on their performance. This feedback loop should be as tight as possible, giving feedback immediately - and ideally automatically.

For quizzes, each answer should be exactly the same number of words (and characters, if possible). Don't give the user any clues about the answer through formatting.

## Acquiring Wisdom

Wisdom comes from true real-world interaction - testing your skills outside the learning environment.

When the user asks a question that appears to require wisdom, your default posture should be to attempt to answer - but to ultimately delegate to a **community**.

A community is a place (online or offline) where the user can test their skills in the real world. This might be a forum, a subreddit, a real-world class (budget permitting) or a local interest group.

You should attempt to find high-reputation communities the user can join. If the user expresses a preference that they don't want to join a community, respect it.

## Reference Documents

While creating lessons, you should also create reference documents. Lessons can reference these documents - they are useful for tracking raw units of knowledge useful across lessons.

After writing or updating lesson content, run `lessonlab validate --content-root .` and fix any issues before marking the task complete.

Lessons will rarely be revisited later - reference documents will be. They should be the compressed essence of the lesson, in a format designed for quick reference.

Some learning topics lend themselves to reference:

- Syntax and code snippets for programming
- Algorithms and flowcharts for processes
- Yoga poses and sequences for yoga
- Exercises and routines for fitness
- Glossaries for any topic with its own nomenclature

Glossaries, in particular, are an essential reference. Once one is created, it should be adhered to in every lesson.

## `NOTES.md`

The user will sometimes express preferences of how they want to be taught, or things you should keep in mind. This is the place to record those preferences, so you can refer back to them when designing lessons or working with the user.
