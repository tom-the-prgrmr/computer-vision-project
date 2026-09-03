---
name: arch-diagram
description: Generates or updates docs/architecture.md with Mermaid diagrams of this project's model architecture and end-to-end processing flow — the diagram deliverable required in the "Sản phẩm nộp" section of docs/requirement_checklist.md. Use when asked for an architecture diagram, pipeline/flow diagram, or when the code structure has changed enough that the existing diagram is stale.
---

# Architecture & pipeline diagrams

Produces `docs/architecture.md`, plain Markdown with GitHub-native Mermaid
fences (`​```mermaid`) — no image files, no Artifact publish, since this has
to render directly on the GitHub repo page per the submission checklist.

## Before drawing

Re-derive the current shape of the system from the actual code, don't draw
from memory of a past version:

- `CLAUDE.md`'s "Architecture" section for the two-layer split (trained
  YOLOv8 detector vs rule-based `angle_rules.py`).
- `app/main.py` for the real request flow (`/predict`, `/predict_video`) —
  check whether it's still a stub (`NotImplementedError`) or implemented, and
  draw what's actually there, not the aspirational TODO version. Note in the
  diagram (or a caption) which parts are still planned vs already wired up.
- `src/pose_scoring/angle_rules.py` for the scoring sub-steps (crop → 33
  MediaPipe landmarks → joint angles → `AngleRange` comparison → tips).
- `src/data/bootstrap_bbox.py` + the v1/v2 dataset strategy in `CLAUDE.md`
  and `docs/problem_statement.md` for the data/training diagram.

## Diagrams to produce

Three separate Mermaid diagrams in `docs/architecture.md`, each with a short
paragraph above it explaining what it shows:

1. **Model architecture** — the two-layer inference pipeline: input image →
   YOLOv8 detector (trained by us, ONNX-exported) → boxes + pose class per
   student → crop each box → MediaPipe Pose (pretrained, not trained by us)
   → 33 landmarks → `angle_rules.score_pose()` (rule-based, `POSE_RULES`
   thresholds) → form OK/issues + tips. Label clearly which boxes are
   "trained" vs "pretrained, off-the-shelf" vs "hand-tuned rules" — that
   distinction is graded (rubric must show a single classification/
   detection/segmentation model; the scoring layer is the separate "own
   idea" item).

2. **End-to-end request flow** — `web/index.html` → `POST /predict` (or
   `/predict_video`) → FastAPI `app/main.py` → model-loaded-once-at-startup
   → per-frame/per-image detect+score loop → JSON response (or annotated
   video) → rendered back in the browser. Use a sequence diagram
   (`sequenceDiagram`) if the request/response shape matters more than
   components; a flowchart (`graph TD`) if the processing steps matter more.

3. **Data & training flow** — v1 (Roboflow YOLO-format download via
   `scripts/download_data.sh`) and v2 (Yoga-82 → `bootstrap_bbox.py`
   pseudo-labels, called out as weak supervision, not ground truth) both
   feeding `notebooks/02_train_detector.ipynb`, producing two checkpoints
   compared in `notebooks/03_evaluation_error_analysis.ipynb`, best one
   exported to ONNX in `notebooks/04_export_onnx.ipynb`. This is the visual
   backing for rubric item 5 (feedback loop).

## Conventions

- Use Mermaid `graph TD`/`graph LR` for pipelines, `sequenceDiagram` for
  request/response flows — don't force everything into one diagram type.
- Keep node labels tied to real file/function names (`YOLOv8 (src/models/)`,
  `score_pose()`, `bootstrap_bboxes()`) so the diagram stays traceable to
  code, not just decorative.
- If `docs/architecture.md` already exists, read it first and update the
  stale parts rather than regenerating everything from scratch — preserve
  any manual notes/captions a human added.
- After writing, mention in the reply which rubric/submission checklist item
  this satisfies (the `rubric-status` skill checks for it) so it doesn't need
  re-deriving.
