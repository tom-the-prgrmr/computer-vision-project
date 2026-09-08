"""SERVICE layer — model inference + business logic. Not a controller: no
HTTP concepts here, just "given image bytes, return detections + form
scores".

Owns the two external resources (ONNX detector, MediaPipe Pose) and
orchestrates them with src/pose_scoring/angle_rules.py. app/controller.py
creates one instance at import time and reuses it for every request —
loading the ONNX session / MediaPipe is the expensive part, never re-create
this per request.
"""

import io
import time

import numpy as np
import onnxruntime
from PIL import Image

from app.schemas import Detection, PredictResponse
from src.models.onnx_inference import RawDetection, run_onnx_detection
from src.pose_scoring.angle_rules import score_pose
from src.pose_scoring.landmark_extraction import extract_landmarks_px, new_pose_model

# Đúng thứ tự index trong data.yaml (data/raw/yoga_v1/data.yaml), đã bỏ
# tiền tố "yoga-pose " -- xem bug thật gặp phải ở Giai đoạn 5
# (docs/specs/g5-feedback-loop.md). Không đọc tên lớp từ file ONNX (không
# đáng tin cậy/không nhất quán giữa các bản export).
DEFAULT_CLASS_NAMES = ["bridge", "downward", "plank", "shoulderstand", "tree"]


class PoseDetectionService:
    def __init__(
        self,
        model_path: str,
        conf_threshold: float = 0.5,
        class_names: list[str] | None = None,
    ):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.class_names = class_names or DEFAULT_CLASS_NAMES
        self._session: onnxruntime.InferenceSession | None = None
        self._pose = None  # mediapipe.solutions.pose.Pose, lazy-loaded

    # ---- lazy loading (runs once, on first real request) ----

    def _ensure_loaded(self) -> None:
        if self._session is not None and self._pose is not None:
            return
        self._session = onnxruntime.InferenceSession(
            self.model_path, providers=["CPUExecutionProvider"]
        )
        self._pose = new_pose_model()

    # ---- the two model calls ----

    def _detect(self, image: np.ndarray) -> list[RawDetection]:
        """`image`: RGB, HWC (từ predict_image() bên dưới)."""
        return run_onnx_detection(self._session, image, self.class_names, self.conf_threshold)

    def _extract_landmarks(self, crop: np.ndarray) -> np.ndarray | None:
        """`crop`: RGB, HWC (slice trực tiếp từ `image` ở predict_image(),
        đã là RGB sẵn -- extract_landmarks_px() nhận thẳng RGB, không cần
        convert gì thêm, xem src/pose_scoring/landmark_extraction.py)."""
        return extract_landmarks_px(crop, self._pose)

    # ---- public API used by app/controller.py ----

    def predict_image(self, image_bytes: bytes) -> PredictResponse:
        start = time.perf_counter()
        self._ensure_loaded()
        image = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))

        detections: list[Detection] = []
        for raw in self._detect(image):
            x1, y1, x2, y2 = (int(v) for v in raw.box)
            crop = image[y1:y2, x1:x2]
            # Box clip có thể suy biến (vd sát rìa ảnh) -> crop rỗng;
            # MediaPipe crash trên ảnh rỗng, coi như không detect được pose.
            landmarks = self._extract_landmarks(crop) if crop.size > 0 else None

            form_ok, tips = None, []
            if landmarks is not None:
                score = score_pose(raw.class_name, landmarks)
                form_ok, tips = score.ok, score.issues

            detections.append(
                Detection(
                    pose=raw.class_name,
                    confidence=raw.confidence,
                    box=list(raw.box),
                    form_ok=form_ok,
                    tips=tips,
                )
            )

        latency_ms = (time.perf_counter() - start) * 1000
        return PredictResponse(detections=detections, latency_ms=latency_ms)

    def predict_video(self, video_bytes: bytes):
        """TODO (T7.7, optional): same detect+score pipeline applied per
        frame. First thing to cut if behind schedule — see docs/PLAN.md
        Buffer."""
        raise NotImplementedError("Optional — implement only if ahead of schedule.")
