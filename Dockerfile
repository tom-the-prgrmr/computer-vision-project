# Dockerfile deploy lên VPS riêng (đứng sau Caddy làm reverse proxy + HTTPS,
# xem docker-compose.yml + Caddyfile) — docs/specs/g9-deploy-public.md.
# Gộp backend FastAPI + web demo tĩnh vào 1 process duy nhất (app/main.py mount
# StaticFiles), không cần server riêng cho web/ khi deploy.
FROM python:3.11-slim

WORKDIR /app

# opencv-python-headless vẫn link tới libGL lúc import dù là bản "headless"
# (không có GUI) — base image slim không có sẵn thư viện đồ hoạ hệ thống
# này, thiếu thì `import cv2` lỗi ImportError: libGL.so.1. libglib2.0-0 đi
# kèm vì cùng nhóm lỗi hay gặp (libgthread-2.0.so.0) với opencv trên image
# Debian tối giản.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Cài dependencies trước, tách layer riêng khỏi code để cache khi code đổi
# mà requirements.txt không đổi.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Chỉ copy đúng những gì runtime cần — không copy data/, notebooks/, .git/
# (xem .dockerignore). models/best.onnx PHẢI có mặt trong build context khi
# build trên VPS (không bị .gitignore chặn ở đó vì build context là thư mục
# thật trên VPS, không phải git clone từ GitHub — xem hướng dẫn rsync/scp ở
# spec T9.4).
COPY app/ ./app/
COPY src/ ./src/
COPY web/ ./web/
COPY models/ ./models/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
