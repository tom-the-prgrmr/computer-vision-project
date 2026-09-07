"""YOLOv8 baseline training wrapper.

Thin wrapper around `ultralytics.YOLO(...).train(...)` so every call site —
baseline (notebooks/02_train_detector.ipynb), ablation (Giai đoạn 3), and the
post-error-analysis retrain (Giai đoạn 5) — shares the same reproducibility
knobs (seed) and the augmentation config chosen in docs/specs/g1-data.md
(T1.5) instead of copy-pasting hyperparameters into each notebook cell.
"""

from typing import Any

from ultralytics import YOLO
from ultralytics.utils.metrics import DetMetrics


def train(
    data: str,
    model: str = "yolov8n.pt",
    epochs: int = 50,
    seed: int = 42,
    imgsz: int = 640,
    flipud: float = 0.0,
    fliplr: float = 0.5,
    degrees: float = 10.0,
    **kwargs: Any,
) -> DetMetrics:
    """Fine-tune a YOLOv8 detector.

    Args:
        data: path to a YOLO-format `data.yaml` (e.g.
            "data/raw/yoga_v1/data.yaml").
        model: base checkpoint to fine-tune from (a `.pt` name Ultralytics
            resolves/downloads, or a path to an existing checkpoint —
            e.g. reuse a v1 `best.pt` when bootstrapping v2).
        epochs: training epochs. Baseline = 50 (docs/specs/g2-baseline-training.md).
        seed: fixed for reproducibility (assignment requirement — see
            docs/REQUIREMENTS.md §4).
        imgsz: training/inference image size in pixels.
        flipud, fliplr, degrees: augmentation knobs chốt ở T1.5 — default
            here so every call site stays consistent unless a caller (e.g.
            the Giai đoạn 3 ablation, which flips augmentation off) opts out
            explicitly.
        **kwargs: forwarded as-is to `YOLO.train()` for anything else
            (e.g. `batch`, `name`, `resume`).

    Returns:
        The `DetMetrics` from the final-epoch validation pass Ultralytics
        runs automatically at the end of `train()` — `.save_dir` points at
        `runs/detect/<name>/` (containing `results.csv`, `results.png`, and
        `weights/{best,last}.pt`), and `.box.map50` / `.box.map` are the
        mAP@0.5 / mAP@0.5:0.95 already computed on `best.pt` — no need to
        reload the checkpoint and call `.val()` again just to read these.
    """
    yolo = YOLO(model)
    return yolo.train(
        data=data,
        epochs=epochs,
        seed=seed,
        imgsz=imgsz,
        flipud=flipud,
        fliplr=fliplr,
        degrees=degrees,
        **kwargs,
    )
