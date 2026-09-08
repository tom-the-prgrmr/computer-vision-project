"""ONNX inference for the YOLOv8 detector: preprocess -> session.run() ->
postprocess. Shared by app/service.py::_detect() (real requests) and
notebooks/04_export_onnx.ipynb T7.2 (latency benchmark) -- same code path
in both places so the benchmark measures what production actually runs.

Ultralytics `model.export(format="onnx")` (no `nms=True`) produces a RAW
output tensor `(1, 4+nc, num_anchors)`: no NMS baked in, and (unlike
YOLOv5) no separate "objectness" column -- column 4: is already per-class
score (post-sigmoid). This module does the NMS + box-rescaling by hand.
"""

from dataclasses import dataclass

import cv2
import numpy as np
import onnxruntime


@dataclass
class RawDetection:
    class_id: int
    class_name: str
    confidence: float
    box: tuple[float, float, float, float]  # x1, y1, x2, y2 in pixel space, ẢNH GỐC


@dataclass
class LetterboxInfo:
    scale: float
    pad_x: float
    pad_y: float
    orig_w: int
    orig_h: int


def preprocess(image: np.ndarray, imgsz: int = 640) -> tuple[np.ndarray, LetterboxInfo]:
    """Letterbox resize (giữ tỉ lệ khung hình, pad màu (114,114,114) căn
    giữa -- đúng quy ước Ultralytics) về (imgsz, imgsz), chuẩn hoá [0,1],
    HWC -> CHW, thêm batch dim -> (1, 3, imgsz, imgsz) float32.

    `image`: RGB, HWC (cùng convention với extract_landmarks_px()).
    """
    orig_h, orig_w = image.shape[:2]
    scale = min(imgsz / orig_w, imgsz / orig_h)
    new_w, new_h = round(orig_w * scale), round(orig_h * scale)
    # Làm tròn pad NGAY Ở ĐÂY và dùng đúng giá trị đã làm tròn cho cả việc
    # đặt ảnh lên canvas lẫn LetterboxInfo trả ra -- nếu để lệch (đặt ảnh
    # theo giá trị đã round nhưng lưu lại giá trị pad float chưa round),
    # lúc dịch box ngược ở postprocess() sẽ trừ sai offset tới 0.5px, lệch
    # thêm khi chia lại cho scale (phát hiện thật qua code-review).
    top, left = round((imgsz - new_h) / 2), round((imgsz - new_w) / 2)

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((imgsz, imgsz, 3), 114, dtype=np.uint8)
    canvas[top : top + new_h, left : left + new_w] = resized

    tensor = canvas.astype(np.float32) / 255.0
    tensor = tensor.transpose(2, 0, 1)[np.newaxis, ...]  # HWC -> CHW -> NCHW
    info = LetterboxInfo(scale=scale, pad_x=left, pad_y=top, orig_w=orig_w, orig_h=orig_h)
    return tensor, info


def postprocess(
    raw_output: np.ndarray,
    letterbox_info: LetterboxInfo,
    class_names: list[str],
    conf_threshold: float,
    iou_threshold: float = 0.45,
) -> list[RawDetection]:
    """`raw_output`: (1, 4+nc, num_anchors) thô từ ONNX session, chưa NMS.
    `class_names` phải đúng thứ tự index model train (không đọc từ ONNX
    metadata -- không đáng tin cậy) và đã bỏ tiền tố "yoga-pose " (xem
    docs/specs/g5-feedback-loop.md). `nc` suy từ raw_output.shape, không
    hardcode -- cho phép smoke-test với model chưa train (nc khác 5).
    """
    predictions = raw_output[0].T  # (4+nc, num_anchors) -> (num_anchors, 4+nc)
    boxes_xywh = predictions[:, :4]  # cx, cy, w, h -- toạ độ letterbox (pixel, imgsz scale)
    class_scores = predictions[:, 4:]

    if class_scores.shape[1] != len(class_names):
        raise ValueError(
            f"Model ONNX có {class_scores.shape[1]} lớp nhưng class_names truyền "
            f"vào có {len(class_names)} phần tử — chắc chắn là 2 model khác nhau "
            f"(vd model chưa train dùng nhầm class_names của model thật, hoặc "
            f"ngược lại). Kiểm tra lại MODEL_PATH khớp với class_names đang dùng."
        )

    class_ids = np.argmax(class_scores, axis=1)
    confidences = class_scores[np.arange(len(class_scores)), class_ids]

    keep = confidences > conf_threshold
    boxes_xywh, class_ids, confidences = boxes_xywh[keep], class_ids[keep], confidences[keep]
    if len(boxes_xywh) == 0:
        return []

    # cx,cy,w,h -> x1,y1,x2,y2 (vẫn toạ độ letterbox)
    cx, cy, w, h = boxes_xywh[:, 0], boxes_xywh[:, 1], boxes_xywh[:, 2], boxes_xywh[:, 3]
    x1, y1, x2, y2 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    boxes_xyxy = np.stack([x1, y1, x2, y2], axis=1)

    detections: list[RawDetection] = []
    # NMS theo từng lớp riêng: 2 học viên khác tư thế có thể chồng box thật,
    # không nên bị NMS gộp-lớp xoá nhầm (xem docs/specs/g7-export-backend.md).
    for class_id in np.unique(class_ids):
        mask = class_ids == class_id
        cls_boxes = boxes_xyxy[mask]
        cls_confidences = confidences[mask]

        # cv2.dnn.NMSBoxes cần box dạng (x, y, w, h) -- không phải xyxy.
        nms_input_boxes = [
            [b[0], b[1], b[2] - b[0], b[3] - b[1]] for b in cls_boxes
        ]
        indices = cv2.dnn.NMSBoxes(
            nms_input_boxes, cls_confidences.tolist(), conf_threshold, iou_threshold
        )
        indices = np.array(indices).flatten() if len(indices) > 0 else []

        for idx in indices:
            box_letterbox = cls_boxes[idx]
            box_orig = _letterbox_box_to_original(box_letterbox, letterbox_info)
            detections.append(
                RawDetection(
                    class_id=int(class_id),
                    class_name=class_names[int(class_id)],
                    confidence=float(cls_confidences[idx]),
                    box=box_orig,
                )
            )

    return detections


def _letterbox_box_to_original(
    box_letterbox: np.ndarray, info: LetterboxInfo
) -> tuple[float, float, float, float]:
    """Dịch box từ toạ độ letterbox (pixel, imgsz scale) về toạ độ ảnh gốc:
    trừ pad, chia scale, clip theo (orig_w, orig_h)."""
    x1, y1, x2, y2 = box_letterbox
    x1 = (x1 - info.pad_x) / info.scale
    y1 = (y1 - info.pad_y) / info.scale
    x2 = (x2 - info.pad_x) / info.scale
    y2 = (y2 - info.pad_y) / info.scale
    x1 = max(0.0, min(x1, info.orig_w))
    y1 = max(0.0, min(y1, info.orig_h))
    x2 = max(0.0, min(x2, info.orig_w))
    y2 = max(0.0, min(y2, info.orig_h))
    return (x1, y1, x2, y2)


def run_onnx_detection(
    session: onnxruntime.InferenceSession,
    image: np.ndarray,
    class_names: list[str],
    conf_threshold: float,
    imgsz: int = 640,
    iou_threshold: float = 0.45,
) -> list[RawDetection]:
    """preprocess -> session.run() -> postprocess, gộp thành 1 lời gọi duy
    nhất -- dùng chung cho app/service.py::_detect() và benchmark T7.2."""
    tensor, letterbox_info = preprocess(image, imgsz=imgsz)
    input_name = session.get_inputs()[0].name
    raw_output = session.run(None, {input_name: tensor})[0]
    return postprocess(raw_output, letterbox_info, class_names, conf_threshold, iou_threshold)
