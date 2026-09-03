"""Request/response models for the prediction API. Pure data shapes only —
no logic here (that's app/service.py).
"""

from pydantic import BaseModel


class Detection(BaseModel):
    pose: str
    confidence: float
    box: list[float]  # x1, y1, x2, y2 in pixel space
    form_ok: bool | None = None
    tips: list[str] = []


class PredictResponse(BaseModel):
    detections: list[Detection]
    latency_ms: float
