---
name: rubric-status
description: Reports progress against this project's 7-step grading rubric by checking docs/requirement_checklist.md against actual repo state (which stubs still raise NotImplementedError, which notebooks/artifacts exist). Use when asked things like "where are we", "rubric status", "checklist progress", "what's left to do", or before a submission/deadline push.
---

# Rubric status check

This project is graded against the 7-item lifecycle rubric in
`docs/requirement_checklist.md` (source: `docs/problem_statement.md`, deadline
15/9). The checklist's `[ ]`/`[x]` boxes are usually stale — this skill
re-derives real status from the repo instead of trusting them, then reports
both.

## Steps

1. Read `docs/requirement_checklist.md` for the 7 items and their target
   files.
2. For each item, gather concrete evidence — don't infer from intentions,
   check what's actually there:

   | # | Item | Evidence to check |
   |---|------|--------------------|
   | 1 | Problem statement | `docs/problem_statement.md` exists with real content (not a stub) |
   | 2 | Data | `notebooks/01_data_exploration.ipynb` exists; `data/raw/yoga_v1/` non-empty (v1 downloaded via `scripts/download_data.sh`) |
   | 3 | Method & Training | `notebooks/02_train_detector.ipynb` exists and has been run (has outputs, not just empty cells); `src/models/` has real training code, not just `__init__.py`; a checkpoint exists under `models/` |
   | 4 | Evaluation & Error Analysis | `notebooks/03_evaluation_error_analysis.ipynb` exists and has been run; look for mAP/confusion-matrix output and at least one concrete misclassified-example analysis |
   | 5 | Feedback loop | evidence of a v1 **vs** v2 comparison with real before/after numbers — `src/data/bootstrap_bbox.py`'s `bootstrap_bboxes()` implemented (not `NotImplementedError`), a second training run logged in notebook 02/03. A UI tip in `angle_rules.py` does **not** count here — flag it if the checklist or writeup conflates the two (the `cv-architecture-review` agent enforces the full rule) |
   | 6 | Own idea (pose scoring) | `src/pose_scoring/angle_rules.py`'s `score_pose()` implemented, `POSE_RULES` calibrated for the final class list |
   | 7 | Deployment | `app/main.py`'s `/predict` and `/predict_video` implemented (not `NotImplementedError`), model loaded once at startup; `notebooks/04_export_onnx.ipynb` exists; `web/index.html` works against a running API; latency/FPS benchmark exists somewhere in docs/notebook |

   Use `Grep` for `NotImplementedError` across `src/` and `app/` to quickly
   spot unfinished stubs, and `Glob`/`Read` to check which notebooks/files
   exist and whether they have real content vs are empty scaffolds.

3. Also check the submission checklist section ("Sản phẩm nộp") the same way:
   README run-from-scratch instructions, architecture + pipeline diagrams in
   `docs/`, slide deck under `docs/slides/`.

4. Report a compact status table: for each of the 7 items + submission
   checklist, ✅ done / 🟡 partial (say what's missing) / ⬜ not started, each
   with the file(s) checked. Call out anything that looks superficially done
   (file exists) but is actually still a stub.

5. Do **not** silently edit `docs/requirement_checklist.md`'s checkboxes.
   Report status in the response; only update the file if the user asks you
   to, since it's their tracking doc and they may want to annotate it
   themselves.
