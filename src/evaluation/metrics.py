"""Confusion-matrix helpers for error analysis.

Ultralytics writes a plotted `confusion_matrix.png` as a side effect of
`model.val()`, but doesn't expose "which class pairs get confused most" as
plain numbers. These two functions fill that gap for
notebooks/03_evaluation_error_analysis.ipynb (T4.1-T4.2): run validation
once, then rank the off-diagonal cells. `per_image_errors()` lists which
images are wrong and how (Giai đoạn 12 error analysis on the clean split).
"""

from pathlib import Path


import numpy as np
from ultralytics import YOLO


def load_confusion_matrix(model_path: str, data_yaml: str, split: str = "val") -> tuple[np.ndarray, list[str]]:
    """Run validation and return the raw confusion matrix + class names.

    Args:
        model_path: path to a trained checkpoint (e.g.
            "runs/detect/yolov8n_v1_baseline/weights/best.pt").
        data_yaml: path to the YOLO data.yaml used for validation.
        split: which data.yaml split to evaluate ("val" or "test").

    Returns:
        (matrix, class_names) — matrix is (nc+1, nc+1): row/col `i` is
        class `class_names[i]` for `i < nc`, plus a trailing "background"
        row/col Ultralytics uses to count missed detections (false
        negatives) and spurious detections (false positives). Matrix rows
        are **predictions**, columns are **ground truth** — i.e.
        `matrix[predicted_class, true_class]` (Ultralytics'
        `ConfusionMatrix.matrix` convention; verified against its own
        `plot()`, which puts "True" on the x-axis/columns and "Predicted"
        on the y-axis/rows).
    """
    model = YOLO(model_path)
    val_results = model.val(data=data_yaml, split=split)
    matrix = val_results.confusion_matrix.matrix
    class_names = [val_results.names[i] for i in range(len(val_results.names))]
    class_names.append("background")
    return matrix, class_names


def top_confused_pairs(
    matrix: np.ndarray,
    class_names: list[str],
    k: int = 3,
    exclude_background: bool = True,
) -> list[tuple[str, str, int]]:
    """Rank off-diagonal confusion-matrix cells, largest count first.

    Args:
        matrix, class_names: from `load_confusion_matrix()`.
        k: max number of pairs to return (fewer if the matrix has fewer
            non-zero off-diagonal cells — a near-perfect model may not
            have 3 confused pairs to report, and that's a valid result).
        exclude_background: skip pairs involving the "background" class
            (missed/spurious detections) to focus on confusion *between*
            real pose classes, which is what T4.2 asks for.

    Returns:
        List of (true_class, predicted_class, count), sorted descending
        by count, non-zero counts only.
    """
    n = len(class_names)
    pairs: list[tuple[str, str, int]] = []
    for pred_idx in range(n):
        for true_idx in range(n):
            if true_idx == pred_idx:
                continue  # diagonal = correct predictions
            if exclude_background and "background" in (class_names[true_idx], class_names[pred_idx]):
                continue
            count = int(matrix[pred_idx, true_idx])  # matrix[predicted, true] — see load_confusion_matrix()
            if count > 0:
                pairs.append((class_names[true_idx], class_names[pred_idx], count))
    pairs.sort(key=lambda p: p[2], reverse=True)
    return pairs[:k]


def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    inter_w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    inter_h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = inter_w * inter_h
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def per_image_errors(
    model: YOLO,
    images_dir: Path,
    labels_dir: Path,
    class_names: list[str],
    conf: float = 0.25,
    iou_threshold: float = 0.5,
) -> list[dict]:
    """Predict every image once and list the ones with at least one error.

    Each ground-truth box is greedily matched to the highest-confidence
    unused prediction with IoU >= iou_threshold:
      - matched, same class  -> correct
      - matched, other class -> "wrong_class" (true -> predicted)
      - unmatched            -> "missed" (false negative)
    Predictions left unmatched -> "spurious" (false positive).

    Returns one dict per image that has any error: {"path", "errors":
    [(kind, true_cls, pred_cls, conf)], "result"} -- `result` is kept so a
    caller can plot it (`result.plot()`) without predicting again.
    """
    image_paths = sorted(p for p in Path(images_dir).iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    erroneous = []
    for image_path in image_paths:
        result = model.predict(source=str(image_path), conf=conf, verbose=False)[0]
        h, w = result.orig_shape
        truths = []
        label_path = Path(labels_dir) / f"{image_path.stem}.txt"
        if label_path.exists():
            for line in label_path.read_text().splitlines():
                parts = line.split()
                if len(parts) == 5:
                    cls_id, x, y, bw, bh = int(parts[0]), *map(float, parts[1:])
                    truths.append((cls_id, ((x - bw / 2) * w, (y - bh / 2) * h, (x + bw / 2) * w, (y + bh / 2) * h)))
        preds = [
            (int(c), float(s), tuple(map(float, box)))
            for c, s, box in zip(result.boxes.cls, result.boxes.conf, result.boxes.xyxy)
        ]

        errors, used = [], set()
        for true_id, true_box in truths:
            candidates = [
                (score, i) for i, (_, score, box) in enumerate(preds) if i not in used and _iou(box, true_box) >= iou_threshold
            ]
            if not candidates:
                errors.append(("missed", class_names[true_id], None, 0.0))
                continue
            score, i = max(candidates)
            used.add(i)
            if preds[i][0] != true_id:
                errors.append(("wrong_class", class_names[true_id], class_names[preds[i][0]], score))
        for i, (pred_id, score, _) in enumerate(preds):
            if i not in used:
                errors.append(("spurious", None, class_names[pred_id], score))

        if errors:
            erroneous.append({"path": image_path, "errors": errors, "result": result})
    return erroneous
