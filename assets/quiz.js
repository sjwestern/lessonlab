document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-check-answer]");
  if (!button) return;

  const item = button.closest(".quiz-item");
  const select = item.querySelector("select");
  const feedback = item.querySelector(".feedback");
  const isCorrect = select.value === item.dataset.answer;

  feedback.textContent = isCorrect
    ? item.dataset.correct
    : item.dataset.incorrect;
  feedback.className = `feedback ${isCorrect ? "correct" : "incorrect"}`;
});

const lesson = document.querySelector("[data-lesson-id]");

if (lesson) {
  const lessonId = lesson.dataset.lessonId;
  const answerControls = [...lesson.querySelectorAll("[data-response-id]")];
  const saveStatus = lesson.querySelector("[data-save-status]");
  const lessonStatus = lesson.querySelector("[data-lesson-status]");
  const submitStatus = lesson.querySelector("[data-submit-status]");
  const submitButton = lesson.querySelector("[data-submit-lesson]");
  let saveTimer;
  let pendingSave = Promise.resolve();
  let restoring = true;

  const answersUrl = `/api/lessons/${lessonId}/answers`;

  function collectAnswers() {
    return Object.fromEntries(
      answerControls.map((control) => [control.dataset.responseId, control.value])
    );
  }

  function collectArtifacts() {
    const fields = [...lesson.querySelectorAll("[data-artifact-field]")];
    if (fields.length === 0) return null;
    const artifacts = { commitRef: "", testNames: [], artifactPaths: [] };
    for (const field of fields) {
      const role = field.dataset.artifactField;
      const value = field.value || "";
      if (role === "commitRef") {
        artifacts.commitRef = value.trim();
      } else if (role === "testNames" || role === "artifactPaths") {
        artifacts[role] = value
          .split("\n")
          .map((line) => line.trim())
          .filter(Boolean);
      }
    }
    return artifacts;
  }

  function showLessonStatus(status) {
    const labels = {
      "not-started": "Not started",
      "in-progress": "In progress",
      submitted: "Submitted for review",
      completed: "Completed",
    };
    lessonStatus.textContent = `Lesson status: ${labels[status] ?? status}`;
  }

  function showSavedAt(updatedAt) {
    if (!updatedAt) {
      saveStatus.textContent = "Answers have not been saved yet.";
      return;
    }
    const savedTime = new Date(updatedAt).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    saveStatus.textContent = `Saved at ${savedTime}.`;
  }

  async function request(url, options = {}) {
    const response = await fetch(url, options);
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || `Request failed: ${response.status}`);
    return body;
  }

  async function saveDraft() {
    saveStatus.textContent = "Saving...";
    try {
      const state = await request(answersUrl, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers: collectAnswers() }),
      });
      showLessonStatus(state.status);
      showSavedAt(state.updatedAt);
    } catch (error) {
      saveStatus.textContent = `Save failed: ${error.message}`;
      throw error;
    }
  }

  function queueSave() {
    if (restoring) return;
    clearTimeout(saveTimer);
    saveStatus.textContent = "Unsaved changes...";
    saveTimer = setTimeout(() => {
      pendingSave = pendingSave.catch(() => {}).then(saveDraft);
    }, 500);
  }

  answerControls.forEach((control) => control.addEventListener("input", queueSave));

  submitButton.addEventListener("click", async () => {
    const missing = answerControls.find(
      (control) => control.required && !control.value.trim()
    );
    if (missing) {
      submitStatus.textContent = "Complete each required answer before submitting.";
      missing.focus();
      missing.reportValidity();
      return;
    }

    clearTimeout(saveTimer);
    submitButton.disabled = true;
    submitStatus.textContent = "Submitting...";
    try {
      await pendingSave.catch(() => {});
      const submitBody = { answers: collectAnswers() };
      const artifacts = collectArtifacts();
      if (artifacts) submitBody.artifacts = artifacts;
      const state = await request(`/api/lessons/${lessonId}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(submitBody),
      });
      showLessonStatus(state.status);
      showSavedAt(state.updatedAt);
      submitStatus.textContent = `Submitted. Ask your teaching agent to review lesson ${lessonId}.`;
    } catch (error) {
      submitStatus.textContent = `Submission failed: ${error.message}`;
    } finally {
      submitButton.disabled = false;
    }
  });

  request(answersUrl)
    .then((state) => {
      for (const control of answerControls) {
        control.value = state.answers[control.dataset.responseId] ?? "";
      }
      showLessonStatus(state.status);
      showSavedAt(state.updatedAt);
    })
    .catch((error) => {
      saveStatus.textContent = `Could not load saved answers: ${error.message}`;
    })
    .finally(() => {
      restoring = false;
    });
}
