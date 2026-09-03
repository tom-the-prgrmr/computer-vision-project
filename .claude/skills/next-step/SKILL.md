---
name: next-step
description: The single entry point for "what should I do now" on this project — finds the current step in docs/PLAN.md (falling back to the 7 rubric items in docs/requirement_checklist.md if there's no PLAN.md). If that step has no spec yet, writes one and stops there for the user to read. If the spec already exists, implements it, runs the cv-architecture-review agent and auto-fixes what it finds, runs a smoke test, and reports exactly how the user should do their own real test — pausing to ask only when something needs a human decision or is outside this environment (external accounts, Colab/GPU execution). Use when asked to continue, do the next step, tiếp tục, làm bước tiếp theo, spec ra 1 bước, or to implement an already-written spec.
---

# Next step

Two-touchpoint cycle: **(1)** the user reads a spec you wrote for the current
step, **(2)** you code + review + smoke-test it, they do the real test
themselves. This skill *is* both calls of that cycle — which one happens
depends on whether a spec already exists when it's invoked. Never commits or
pushes — always leaves the working tree dirty for the user to inspect.

## 1. Find the current step

If `docs/PLAN.md` exists: walk its `## Giai đoạn N — ...` sections in order,
find the first with unchecked `- [ ]` tasks — that's current (key it as
`g<N>-<slug>`, slug from the Giai đoạn name). If a Giai đoạn is marked "song
song" with another that's also incomplete, both are candidates — say so and
ask which to work on, don't silently pick one.

If there's no `docs/PLAN.md`, fall back to the 7 rubric items in
`docs/requirement_checklist.md` (key `<NN>-<slug>`, `01-problem-statement` …
`07-deployment`) — same mechanics below, just without task-level detail to
draw from.

If the user named a specific step, use that instead of auto-detecting.

Report where things stand before doing anything else: which step, which
tasks are already done vs remaining.

If **every** remaining task in this step needs something outside this
environment — an external account/API key, running a notebook cell on
Colab, GPU hardware not available here — say so plainly, list exactly what
the user needs to go do, and stop. Don't invent code work to look useful
when the real blocker is an external action; independent tasks that *are*
code stay in scope even if others in the same step are blocked.

## 2. Spec check — this is touchpoint 1

Check for `docs/specs/<key>-<slug>.md`.

- **Missing, or stale** (the step's task list changed since it was written,
  or it only covers already-completed tasks) → write/update it now, then
  **stop here** — don't implement in the same turn. This stop *is* the
  user's cue to go read it; no chat confirmation question, no Status gate.
  Ground it in real material, don't invent from scratch — the PLAN.md Giai
  đoạn section (or the rubric item text + `docs/problem_statement.md` in the
  no-PLAN.md fallback) already has the goal and file list; also check
  `CLAUDE.md` for architecture rules bearing on this step (e.g. a
  training-phase step is about the *detector*, not UI tips; the pose-scoring
  step has no accuracy metric of its own) and `Glob`/`Grep` what already
  exists so the spec proposes the next concrete increment.

  Save as:

  ```markdown
  # Spec — <key>. <step name> (rubric: <which of the 7 items this feeds>)

  **Plan source:** `docs/PLAN.md` — Giai đoạn <N> (or rubric item <NN>)
  **Status:** draft <!-- draft -> implemented (set at close-out) -->

  ## Mục tiêu
  <What this step needs to produce.>

  ## Việc cụ thể
  <One item per task, each expanded into a concrete acceptance criterion —
  how to tell it's actually done. Pin down anything the source left vague
  (e.g. "epochs baseline (vd 50)" -> an actual chosen number, with a
  one-line reason if it matters).>

  ## File/module liên quan
  <Bullet list of files this step touches.>

  ## Bằng chứng / số liệu kỳ vọng
  <What output proves this step is done — a metric, a figure, a
  before/after table.>

  ## Cách bạn tự test sau khi tôi xong
  <How the user will verify this for real once implementation is done —
  matching whatever manual test PLAN.md already names for this step (curl,
  browser, real camera, Colab run), so this gets pinned down before coding
  starts, not improvised at the end.>

  ## ❓ Quyết định cần bạn chốt
  <Anything genuinely ambiguous this spec should NOT guess at — a threshold,
  a tradeoff, an external dependency. Empty if none; don't invent
  uncertainty that isn't there.>

  ## Rủi ro / điều cần lưu ý
  <Known unknowns/risks that don't block starting but matter.>
  ```

  Tell the user the spec is ready to read and that running this again
  starts implementation.

- **Exists and still covers the remaining tasks** → this is touchpoint 2.
  Re-read it (don't rely on memory). If "❓ Quyết định cần bạn chốt" is
  non-empty, that's the one thing worth stopping for — ask exactly those
  questions, fold the answers into the spec, then continue in the same
  turn. Otherwise go straight to step 3, no other confirmation needed —
  a spec that exists and reads clean is implicitly ready; the user reading
  it *was* the review.

## 3. Implement

Follow the spec's "Việc cụ thể" and "File/module liên quan". Ground rules
from `CLAUDE.md` apply throughout (re-read it if it's been a while):

- Replace the relevant `NotImplementedError` stubs with real implementations
  rather than adding parallel new functions.
- Keep the two-layer split intact (trained YOLO vs rule-based
  `angle_rules.py`) and don't let rubric item 5 (detector feedback loop, real
  before/after numbers) blur with item 6 (pose-scoring tips, no accuracy
  metric of its own) — `cv-architecture-review` enforces the exact
  boundaries, but get it right the first time.
- Logic `app/` will also need goes in `src/`, called from notebooks, not
  duplicated inside a notebook cell.
- If a target file's internal shape isn't obvious from the spec alone,
  design it first — function/class signatures, the data shape flowing
  between them, edge cases — as stubs (signatures + docstrings +
  `NotImplementedError`, matching this repo's existing stub style) before
  filling in real bodies, rather than guessing structure as you go.
- A task needing something outside this environment (external account/API
  key, a Colab/GPU run) isn't something to fake or skip silently — say so,
  tell the user what to go do, and stop that task (other independent tasks
  continue).

**Stop and ask** the moment you hit a genuine implementation decision the
spec didn't pin down — an unclear parameter with real tradeoffs, a missing
input the spec assumed would exist, two reasonable approaches with no stated
preference. Don't guess. This is distinct from review/test findings in steps
4–5, which get auto-fixed without asking — this is about choices made while
writing the first draft, before there's anything to review yet.

## 4. Review, auto-fix, re-review once

Run the `cv-architecture-review` agent against the diff (`git diff`,
working tree). If the change also plausibly has generic correctness issues
beyond the architecture-specific checks, also run the `code-review` skill at
`medium` level. Apply a fix for every finding directly (no per-finding
confirmation — this level of autonomy was the explicit choice for this
command), then re-run `cv-architecture-review` once more.

- Second pass clean → step 5.
- Second pass still finds something → stop, don't loop a third time. Report
  what's left and ask how to proceed.

## 5. Smoke test

Run whatever automated check is actually possible in this environment for
what you just built — don't skip this step, and don't fake a result you
didn't get:

- Pure Python logic (e.g. `score_pose()`, `joint_angle()`) → invoke it
  directly via a quick script/`python -c` with synthetic or sample input,
  confirm it runs without error and the output is sane.
- FastAPI endpoints → `fastapi.testclient.TestClient` (or start `uvicorn`
  briefly and `curl`) against a real or synthetic upload.
- Anything that needs data/GPU/notebooks not available here (Colab
  training, the real dataset) → the honest smoke test is import/syntax
  validity only (`python -m py_compile`, or importing the module) — say
  plainly that real execution needs to happen where the resources are.

If the smoke test fails, treat it like a review finding: fix, re-run once.
If it still fails, stop and report rather than looping.

Then write out, concretely, how the user does **their own real test** —
reuse the spec's "Cách bạn tự test" section (a `curl` command, a URL to
open, "chạy notebook cell X trên Colab", "thử camera trên điện thoại thật").
Be specific enough they can just do it, not a vague "hãy tự kiểm tra lại".

## 6. Close out

Set the spec's `**Status:** implemented`, append "## Implementation notes"
(files touched, what review/smoke-test caught and fixed, anything deferred —
including tasks stopped in step 3 for being outside this environment, so
they aren't lost). If the spec came from a PLAN.md Giai đoạn, tick `[x]` for
each finished task there, leave deferred ones unchecked. Do not commit.

Report what got done, the smoke-test result, the exact steps for the user's
own real test, what's still open in this step, and what the next step will
be — don't auto-start it, the user runs this again when ready. Suggest
`rubric-status` to confirm overall progress, and `arch-diagram` if the
change altered how components connect.
