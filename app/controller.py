"""CONTROLLER — HTTP routes only: parse the request, call the service, shape
the response. Model/business logic lives in app/service.py.
"""

import os

from fastapi import APIRouter, File, UploadFile

from app.schemas import PredictResponse
from app.service import PoseDetectionService

router = APIRouter()

# One service instance for the whole process, reused across every request.
# Loading the model itself happens lazily inside it (see app/service.py),
# not here.
service = PoseDetectionService(
    model_path=os.getenv("MODEL_PATH", "models/best.onnx"),
    conf_threshold=float(os.getenv("DETECTOR_CONF_THRESHOLD", "0.5")),
)


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/predict", response_model=PredictResponse)
async def predict(image: UploadFile = File(...)) -> PredictResponse:
    image_bytes = await image.read()
    return service.predict_image(image_bytes)


@router.post("/predict_video")
async def predict_video(video: UploadFile = File(...)):
    video_bytes = await video.read()
    return service.predict_video(video_bytes)
