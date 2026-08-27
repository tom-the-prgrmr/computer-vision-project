# Yoga Pose Detection & Form Scoring

Mini project cuối module Computer Vision (AI Engineer K08-0226). Phát hiện +
phân loại tư thế yoga của học viên qua ảnh/video, chấm điểm form bằng phân tích
góc khớp, và triển khai thành API + web demo.

Chi tiết bài toán: [`docs/problem_statement.md`](docs/problem_statement.md)
Checklist bám sát đề bài: [`docs/requirement_checklist.md`](docs/requirement_checklist.md)

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
2. **Train**: `notebooks/02_train_detector.ipynb` hoặc `python -m src.models.train`
3. **Eval / error analysis**: `notebooks/03_evaluation_error_analysis.ipynb`
4. **Export ONNX**: `notebooks/04_export_onnx.ipynb`
5. **Serve API**: `uvicorn app.main:app --reload`
6. **Web demo**: mở `web/index.html`, trỏ tới API đang chạy (mặc định `localhost:8000`)

## Trạng thái

Đang ở giai đoạn khởi tạo scaffold — xem tiến độ chi tiết tại
[`docs/requirement_checklist.md`](docs/requirement_checklist.md).
