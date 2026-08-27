"""FastAPI service: image in -> detected pose(s) + form score out.

Run: uvicorn app.main:app --reload
"""

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Yoga Pose Detection & Form Scoring")

# Loose CORS for the local web demo; tighten before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Detection(BaseModel):
    pose: str
    confidence: float
    box: list[float]  # x1, y1, x2, y2
    form_ok: bool | None = None
    tips: list[str] = []


class PredictResponse(BaseModel):
    detections: list[Detection]
    latency_ms: float


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
async def predict(image: UploadFile = File(...)) -> PredictResponse:
    """TODO:
    1. load ONNX-exported YOLO model once at startup (not per-request)
    2. run detection on the uploaded image
    3. for each box, crop + run MediaPipe Pose + src.pose_scoring.angle_rules.score_pose
    4. return detections with form_ok/tips filled in
    """
    raise NotImplementedError("Wire up once the detector is trained and exported to ONNX.")
