# Requirement Checklist — Mini Project Computer Vision

Nguồn: đề bài Google Classroom "Mini Project - Computer Vision Module" (hạn 15/9).
Bản gốc đã lưu tại `docs/reference/`.

Đánh dấu `[x]` khi hoàn thành từng mục, ghi file/notebook tương ứng để dễ trace khi
viết README và làm slide.

## 7 mục bắt buộc (vòng đời)

- [x] **1. Problem statement** — `docs/problem_statement.md`
- [x] **2. Data** — nguồn, số lượng, chia train/val/test, imbalance, augmentation
      → `notebooks/01_data_exploration.ipynb`
- [x] **3. Method & Training** — model + lý do chọn, ≥1 ablation (biến đổi 1 yếu
      tố, seed cố định), log huấn luyện thật
      → `notebooks/02_train_detector.ipynb`, `src/models/train.py`
- [x] **4. Evaluation & Error Analysis** — mAP/confusion matrix, case sai cụ thể +
      Grad-CAM, pattern lỗi lặp lại
      → `notebooks/03_evaluation_error_analysis.ipynb`
- [x] **5. Feedback loop – cải tiến** — mục 4 không tìm ra lỗi trong tập test cùng
      phân bố (0 cặp lớp bị nhầm), nên đổi hướng: đo lỗi thật trên ảnh **ngoài**
      phân bố dataset (OOD) — kết quả: 17/18 = 94.4%, không có pattern lỗi rõ
      rệt → kết luận baseline đã robust, không cần retrain (xem
      `docs/problem_statement.md` mục "Feedback loop cải tiến")
      → `notebooks/05_feedback_loop_ood.ipynb`
- [x] **6. Phần tự nghĩ thêm** — lớp chấm điểm form bằng góc khớp MediaPipe,
      hiệu chỉnh ngưỡng bằng số đo thật trên 15 ảnh mẫu (5 lớp v1), test
      14/15 ảnh đúng form + 5/5 case tổng hợp lệch góc
      → `src/pose_scoring/angle_rules.py`, `scripts/calibrate_pose_rules.py`
- [x] **7. Deployment** — export ONNX, FastAPI (`app/service.py` implement thật,
      test end-to-end qua curl + Playwright pass), benchmark latency/FPS
      thật (GPU T4 Colab + CPU local + CPU Render), web demo xử lý video
      bằng cách gọi lặp lại `/predict` mỗi frame phía client (không có
      endpoint `/predict_video` streaming riêng — optional T7.7, không
      làm vì ngoài buffer thời gian, xem "Xử lý video" trong
      `docs/problem_statement.md`), **deploy public thật** (Render +
      Cloudflare Pages), camera xác nhận chạy đúng trên iPhone thật qua
      HTTPS công khai
      → `notebooks/04_export_onnx.ipynb`, `app/`, `web/`, `docs/specs/g9-deploy-public.md`

## Sản phẩm nộp

- [ ] GitHub repo public *(cần bạn tự xác nhận repo đã set Public trên GitHub)*
  - [x] Toàn bộ code (notebook/script train, eval, export, FastAPI, web demo)
  - [x] README hướng dẫn chạy lại từ đầu (setup, train, serve)
  - [x] Sơ đồ kiến trúc model + sơ đồ luồng xử lý end-to-end (`docs/architecture.md`)
  - [x] Tài liệu mô tả đầy đủ 7 mục ở trên (`docs/problem_statement.md`)
  - [x] 1 bộ slide tóm tắt dự án (`docs/slides/presentation.html` — trình chiếu được; `docs/slides/summary.md` — dàn ý)
- [ ] Video trình bày 5–10 phút, nộp trên Google Classroom, kèm link GitHub
      (bài toán → dữ liệu → cách làm → kết quả → lỗi & bài học → demo chạy thật)
      — Giai đoạn 11, chưa làm

## Lưu ý khi chấm
Không cần SOTA. Trọng tâm: hiểu đúng vòng đời, có lý do cho mỗi lựa chọn, biết rõ
điểm yếu và hướng cải thiện tiếp theo. Rubric: 5 tiêu chí • 100 điểm (xem chi tiết
trực tiếp trên Classroom, mục "Xem hướng dẫn").
