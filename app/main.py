"""FastAPI entrypoint — app assembly only.

Routes: app/controller.py. Model/business logic: app/service.py. Data
shapes: app/schemas.py.

Run: uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controller import router

app = FastAPI(title="Yoga Pose Detection & Form Scoring")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only — narrow to the real frontend domain before deploy (docs/PLAN.md T9.3)
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
