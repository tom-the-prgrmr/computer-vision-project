# Yoga Pose Detection & Form Scoring

Mini project cuối module Computer Vision (AI Engineer K08-0226). Phát hiện +
phân loại tư thế yoga của học viên qua ảnh/video, chấm điểm form bằng phân tích
góc khớp, và triển khai thành API + web demo.

**Requirement đầy đủ (nguồn chân lý)**: [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md)
Chi tiết bài toán (dùng cho mục 1 khi nộp bài): [`docs/problem_statement.md`](docs/problem_statement.md)
Checklist bám sát rubric đề bài: [`docs/requirement_checklist.md`](docs/requirement_checklist.md)

## Kiến trúc

```
Ảnh/video học viên
      │
      ▼
YOLOv8 (fine-tuned) ── model trainable chính
      │  detect + classify tư thế (bounding box + class)
      ▼
MediaPipe Pose (pretrained) ── trích 33 keypoint trong từng box
      │
      ▼
Rule-based angle scoring ── so góc khớp với ngưỡng chuẩn từng tư thế
      │
      ▼
Điểm form + gợi ý cải thiện ──► FastAPI ──► Web demo
```

## Cấu trúc thư mục

```
data/               raw/processed data (gitignored, xem scripts/download_data.sh)
notebooks/          01 data exploration, 02 train, 03 eval & error analysis, 04 export
src/
  data/             bootstrap_bbox.py — sinh bbox cho v2 (15-20 lớp) từ Yoga-82
  models/           train.py — wrapper train YOLOv8
  evaluation/       metrics.py — mAP, confusion matrix, Grad-CAM helpers
  pose_scoring/      angle_rules.py — góc khớp + ngưỡng chuẩn từng tư thế
app/                FastAPI service (inference + scoring)
web/                Web demo tĩnh (upload ảnh/webcam)
docs/               problem statement, checklist, sơ đồ, slides, reference gốc đề bài
models/             checkpoint / .onnx export (gitignored)
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Chạy lại từ đầu

1. **Tải dữ liệu**: `scripts/download_data.sh` (Roboflow v1, 5 lớp)
2. **Train**: `notebooks/02_train_detector.ipynb` (gọi `train()` từ
   `src/models/train.py` — không có CLI riêng, chỉ dùng qua notebook)
3. **Eval / error analysis**: `notebooks/03_evaluation_error_analysis.ipynb`
4. **Export ONNX**: `notebooks/04_export_onnx.ipynb`
5. **Serve API + web demo**: `uvicorn app.main:app --reload` — 1 lệnh duy
   nhất, phục vụ cả `GET /` (trang demo, mount từ `web/`) lẫn `/predict`
   cùng process, mở `http://localhost:8000/`. (Cách cũ chạy 2 server tách
   — `python -m http.server 8080 --directory web` cho web + uvicorn riêng
   cho API — vẫn dùng được cho local dev nếu muốn, xem
   `docs/specs/g8-web-demo.md`.)
6. **Web demo**: tab "Camera trực tiếp" (chính, dùng camera điện
   thoại/iPhone qua `getUserMedia`) hoặc tab "Upload ảnh" (test nhanh).
   `API_BASE` trong `web/index.html` tự nhận diện môi trường, không cần sửa
   tay. ⚠️ Camera trên điện thoại **chỉ hoạt động qua HTTPS** (hoặc
   `localhost` lúc dev) — xem ràng buộc HTTPS/CORS trong
   `docs/REQUIREMENTS.md` mục 7.

## Deploy (Render + Cloudflare Pages, free)

Xem đầy đủ trong [`docs/specs/g9-deploy-public.md`](docs/specs/g9-deploy-public.md)
— lịch sử đổi host 2 lần (HF Spaces → VPS riêng → phương án chính hiện
tại) đều ghi rõ trong đó. Tóm tắt phương án chính: **backend trên
[Render](https://render.com/)** (free web service, build thẳng từ
`Dockerfile`), **frontend tĩnh trên
[Cloudflare Pages](https://pages.cloudflare.com/)** (free, trỏ vào thư mục
`web/`) — cả hai không cần thẻ, tự có HTTPS.

1. Track `models/best.onnx` bằng Git LFS (Render build thẳng từ GitHub repo
   này; `.gitignore` đã có sẵn ngoại lệ `!models/best.onnx` cho đúng 1 file
   này — không cần tự sửa `.gitignore`):
   ```bash
   git lfs install && git lfs track "models/best.onnx"
   git add .gitattributes models/best.onnx && git commit -m "Track model qua Git LFS" && git push
   ```
2. Render: New → Web Service → connect repo này → tự nhận `Dockerfile` →
   instance **Free** → Deploy. Lấy URL `https://<service>.onrender.com`.
3. Cloudflare Pages: Create project → connect repo này → build output
   directory `web`, không cần build command → Deploy. Lấy URL
   `https://<project>.pages.dev`.
4. Sửa `BACKEND_URL` trong `web/index.html` thành URL Render ở bước 2,
   commit + push. Set env `ALLOWED_ORIGINS` trên Render = URL Cloudflare
   Pages ở bước 3.

⚠️ Render free tier ngủ sau ~15 phút không dùng — mở thử trang trước
~1 phút để "đánh thức" trước khi demo/quay video, tránh chờ giữa chừng.

Có sẵn phương án thay thế dùng VPS riêng + Caddy (đã build + review xong,
xem `docker-compose.yml`/`Caddyfile` + chi tiết trong
`docs/specs/g9-deploy-public.md`) nếu Render free không đủ ổn định.

## Trạng thái

Đang ở giai đoạn khởi tạo scaffold — xem tiến độ chi tiết tại
[`docs/requirement_checklist.md`](docs/requirement_checklist.md).
