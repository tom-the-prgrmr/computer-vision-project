"""FastAPI entrypoint — app assembly only.

Routes: app/controller.py. Model/business logic: app/service.py. Data
shapes: app/schemas.py.

Run: uvicorn app.main:app --reload
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.controller import router

app = FastAPI(title="Yoga Pose Detection & Form Scoring")

# "*" mặc định (dev local). Khi đã có URL frontend thật (docs/specs/g9-deploy-public.md
# T9.4 bước 5 — Cloudflare Pages), set env ALLOWED_ORIGINS (comma-separated)
# trong Render Environment settings để siết đúng domain — không hardcode
# domain chưa tồn tại lúc viết code.
_allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"]
    if _allowed_origins == "*"
    else [o.strip() for o in _allowed_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Serve web/index.html (+ mọi asset tĩnh khác trong web/) cùng process với
# API — phải mount SAU include_router(), không thì "/" nuốt mất /health,
# /predict. Cho phép 1 lệnh `uvicorn app.main:app` duy nhất vừa chạy API vừa
# serve trang demo (dùng khi deploy; cách 2-server tách rời của Giai đoạn 8
# vẫn dùng được cho local dev, không bị thay thế).
app.mount("/", StaticFiles(directory="web", html=True), name="web")
