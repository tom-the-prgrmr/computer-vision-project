"""YOLOv8 -> ONNX export wrapper. Thin, same spirit as `train.py::train()` --
notebooks/04_export_onnx.ipynb (T7.1) và bất kỳ chỗ nào khác cần export đều
gọi hàm này thay vì lặp lại `YOLO(...).export(...)`.
"""

from ultralytics import YOLO


def export_onnx(model_path: str, imgsz: int = 640, **kwargs) -> str:
    """Export 1 checkpoint `.pt` sang ONNX.

    Args:
        model_path: đường dẫn checkpoint đã train (vd
            "runs/detect/yolov8n_v1_baseline/weights/best.pt").
        imgsz: phải khớp `imgsz` lúc train (mặc định 640, xem
            `src/models/train.py::train()`) -- lệch imgsz giữa train và
            export không lỗi ngay nhưng làm model kém chính xác hơn.
        **kwargs: forward tới `YOLO.export()` (vd `opset`, `simplify`).
            Không truyền `nms=True` -- `src/models/onnx_inference.py` tự
            làm NMS theo từng lớp, xem docs/specs/g7-export-backend.md.

    Returns:
        Đường dẫn file `.onnx` vừa export (cùng thư mục với `model_path`).
    """
    yolo = YOLO(model_path)
    onnx_path = yolo.export(format="onnx", imgsz=imgsz, **kwargs)
    return str(onnx_path)
