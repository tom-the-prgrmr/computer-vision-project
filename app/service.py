"""SERVICE layer — model inference + business logic. Not a controller: no
HTTP concepts here, just "given image bytes, return detections + form
scores".

Owns the two external resources (ONNX detector, MediaPipe Pose) and
orchestrates them with src/pose_scoring/angle_rules.py. app/main.py creates
one instance at import time and reuses it for every request — loading the
ONNX session / MediaPipe is the expensive part, never re-create this per
request.
"""

import io
import time
from dataclasses import dataclass

import numpy as np
from PIL import Image

from app.schemas import Detection, PredictResponse
from src.pose_scoring.angle_rules import score_pose


@dataclass
class RawDetection:
    class_id: int
    class_name: str
    confidence: float
    box: tuple[float, float, float, float]  # x1, y1, x2, y2 in pixel space


class PoseDetectionService:
    def __init__(self, model_path: str, conf_threshold: float = 0.5):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self._session = None  # onnxruntime.InferenceSession, lazy-loaded
        self._pose = None  # mediapipe.solutions.pose.Pose, lazy-loaded

    # ---- lazy loading (runs once, on first real request) ----

    def _ensure_loaded(self) -> None:
        if self._session is not None and self._pose is not None:
            return
        raise NotImplementedError(
            "TODO: load once — "
            "self._session = onnxruntime.InferenceSession(self.model_path) "
            "(docs/PLAN.md T7.4, needs the export from T7.1); "
            "self._pose = mediapipe.solutions.pose.Pose(static_image_mode=True) (T6.3)."
        )

    # ---- the two model calls ----

    def _detect(self, image: np.ndarray) -> list[RawDetection]:
        """TODO (T7.5): preprocess `image` -> run ONNX session -> postprocess
        (NMS if not already baked into the export) -> list[RawDetection]."""
        raise NotImplementedError("Wire up once the ONNX model is available.")

    def _extract_landmarks(self, crop: np.ndarray) -> np.ndarray | None:
        """TODO (T6.3): run MediaPipe on the cropped student box, return a
        (33, 2) array of pixel-space landmarks, or None if no pose found."""
        raise NotImplementedError("Wire up alongside src/pose_scoring/angle_rules.py.")

    # ---- public API used by app/main.py ----

    def predict_image(self, image_bytes: bytes) -> PredictResponse:
        start = time.perf_counter()
        self._ensure_loaded()
        image = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))

        detections: list[Detection] = []
        for raw in self._detect(image):
            x1, y1, x2, y2 = (int(v) for v in raw.box)
            crop = image[y1:y2, x1:x2]
            landmarks = self._extract_landmarks(crop)

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
