"""Confusion-matrix helpers for error analysis.

Ultralytics writes a plotted `confusion_matrix.png` as a side effect of
`model.val()`, but doesn't expose "which class pairs get confused most" as
plain numbers. These two functions fill that gap for
notebooks/03_evaluation_error_analysis.ipynb (T4.1-T4.2): run validation
once, then rank the off-diagonal cells.
"""

import numpy as np
from ultralytics import YOLO


def load_confusion_matrix(model_path: str, data_yaml: str) -> tuple[np.ndarray, list[str]]:
    """Run validation and return the raw confusion matrix + class names.

    Args:
        model_path: path to a trained checkpoint (e.g.
            "runs/detect/yolov8n_v1_baseline/weights/best.pt").
        data_yaml: path to the YOLO data.yaml used for validation.

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
    val_results = model.val(data=data_yaml)
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
