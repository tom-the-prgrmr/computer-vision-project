# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Mini project for the "Computer Vision Module" course assignment (AI Engineer
K08-0226): detect + classify a student's yoga pose in an image/video, then
score their form and suggest fixes. The full assignment brief and grading
checklist live in `docs/problem_statement.md` and `docs/requirement_checklist.md`
— read those before making architectural changes, since the deliverables are
graded against a specific 7-step rubric (problem statement → data → training
→ evaluation/error analysis → improvement loop → own idea → deployment), not
just "does it work."

The repo is currently a scaffold: directory structure and stub modules are in
place, but the detector isn't trained yet and most functions raise
`NotImplementedError` with a TODO describing what goes there. There is no
build/lint/test tooling configured yet — don't assume `pytest`/`ruff`/etc.
exist until they're actually added.

## Architecture — two independent layers, don't conflate them

1. **Trained model (the one that must go through the full ML lifecycle):
   YOLOv8 object detection**, fine-tuned so each class *is* a pose name
   (Tree, Warrior II, Plank, ...). One model does localization ("where is the
   student") and classification ("which pose") in a single step — this is
   intentional, it's what satisfies the assignment's "must be one of
   classification / detection / segmentation" constraint while still
   supporting multi-student frames. Training/eval/export code lives in
   `src/models/`, `src/evaluation/`, and `notebooks/02`–`04`.

2. **Rule-based form scoring (`src/pose_scoring/angle_rules.py`), not a
   trained model.** For each YOLO detection box, crop it, run pretrained
   MediaPipe Pose to get 33 landmarks, compute joint angles, and compare
   against per-pose `AngleRange` thresholds in `POSE_RULES`. This layer has
   no accuracy/F1 of its own — it's the assignment's "own idea" component
   (rubric item 6), not part of the trained-model evaluation. Don't add
   training code here or try to give it conventional ML metrics.

**Important distinction baked into the rubric — keep these separate:**
- Rubric item 5 ("Feedback loop") = improving the *YOLO detector* itself
  after error analysis (e.g. the v1 → v2 dataset expansion below), measured
  with real before/after numbers (mAP etc.).
- The "gợi ý cải thiện" (tip) a user sees from `angle_rules.py` is a
  *product feature* for the yoga student, not a model-improvement step.
  Don't count UI tips as satisfying rubric item 5.

## Dataset strategy: v1 → v2

- **v1** (default, low-risk): 5 pose classes with ready-made YOLO-format
  bounding boxes from Roboflow ("YOLO YOGA Dataset"). Downloaded via
  `scripts/download_data.sh` (needs `ROBOFLOW_API_KEY` env var) into
  `data/raw/yoga_v1/`.
- **v2** (stretch, needs a GPU beyond free-tier Colab): 15–20 classes,
  bootstrapped from the Yoga-82 *classification* dataset by running a
  pretrained person detector over each image and re-labeling the resulting
  box with the image's existing pose class — see the module docstring in
  `src/data/bootstrap_bbox.py` for the exact steps. These are pseudo-labels,
  not human-verified ground truth; spot-check before trusting them, and say
  so explicitly in the writeup.
- Comparing v1 vs v2 training runs is the intended evidence for rubric item
  5 (Feedback loop).

## Pipeline wiring (currently stubbed)

`app/main.py` (FastAPI, `POST /predict`) is meant to: load the ONNX-exported
YOLO model once at startup → run detection on the uploaded image → for each
box, crop + MediaPipe + `score_pose()` from `angle_rules.py` → return boxes
with pose, confidence, and form tips. `web/index.html` is a single static
page that posts an image to `http://localhost:8000/predict` and dumps the
JSON response — no build step, open it directly in a browser once the API is
running.

## Commands

```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# v1 data (requires ROBOFLOW_API_KEY)
bash scripts/download_data.sh

# once training/export are implemented:
uvicorn app.main:app --reload      # serves POST /predict on :8000
```

Training/eval/export are meant to be driven from the notebooks in
`notebooks/` (`01_data_exploration` → `02_train_detector` →
`03_evaluation_error_analysis` → `04_export_onnx`); mirror any logic that
needs to be reused by `app/` into `src/` rather than importing notebooks.
