"""FastAPI entrypoint.

CONTROLLER layer lives in this file: HTTP routes only — parse the request,
call the service, shape the response. All detection/scoring logic lives in
app/service.py (SERVICE layer). Data shapes: app/schemas.py.

Run: uvicorn app.main:app --reload
"""

import os

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import PredictResponse
from app.service import PoseDetectionService

# ---- SERVICE (model layer) — one instance for the whole process, reused
# across every request. Loading the model happens lazily inside it, not here.
service = PoseDetectionService(
    model_path=os.getenv("MODEL_PATH", "models/best.onnx"),
    conf_threshold=float(os.getenv("DETECTOR_CONF_THRESHOLD", "0.5")),
)

# ---- CONTROLLER (HTTP layer) ----
app = FastAPI(title="Yoga Pose Detection & Form Scoring")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only — narrow to the real frontend domain before deploy (docs/PLAN.md T9.3)
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
async def predict(image: UploadFile = File(...)) -> PredictResponse:
    image_bytes = await image.read()
    return service.predict_image(image_bytes)


@app.post("/predict_video")
async def predict_video(video: UploadFile = File(...)):
    video_bytes = await video.read()
    return service.predict_video(video_bytes)
