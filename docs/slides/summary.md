<!--
Slide tóm tắt dự án — dùng làm dàn ý quay video Giai đoạn 11 (T11.1-T11.3).
Format: mỗi `---` là 1 slide (tương thích Marp/reveal.js nếu cần convert
sau: `marp docs/slides/summary.md --pdf`). Số liệu lấy từ
docs/problem_statement.md, không đo lại ở đây.

Bản trình chiếu thật, cùng nội dung, 2 định dạng:
- docs/slides/presentation.html — mở trực tiếp trong trình duyệt, điều
  hướng bằng phím mũi tên.
- docs/slides/presentation.pptx — PowerPoint chuẩn, mở bằng
  PowerPoint/Google Slides/LibreOffice Impress, chỉnh sửa tay được (sinh
  từ scripts/build_pptx.py qua python-pptx).
File này (.md) là dàn ý/nội dung gốc.
-->

# Yoga Pose Detection & Form Scoring

Mini Project — Computer Vision Module (AI Engineer K08-0226)

Phát hiện + phân loại tư thế yoga qua ảnh/video, chấm điểm form, deploy
thành web demo public.

---

## 1. Bài toán

- Input: ảnh/video học viên tập yoga.
- Output: vị trí + tên tư thế (5 lớp: bridge, downward, plank,
  shoulderstand, tree) + đánh giá form đúng/sai + gợi ý sửa.
- Ràng buộc đề bài: phải có 1 model classification/detection/segmentation
  **tự train** — chọn **YOLOv8 detection** (vừa localize vừa classify
  trong 1 bước, hỗ trợ nhiều học viên/khung hình).

---

## 2. Kiến trúc — 2 lớp độc lập

1. **YOLOv8 (tự train, ONNX-exported)** — detect + classify tư thế.
2. **MediaPipe Pose (pretrained) + rule-based angle scoring (tự nghĩ)** —
   crop box → 33 keypoint → so góc khớp với ngưỡng chuẩn từng tư thế →
   tip sửa form.

Sơ đồ đầy đủ: `docs/architecture.md`.

---

## 3. Dữ liệu

- **v1** (dùng thật): 5 lớp, YOLO-format có sẵn bbox, tải từ Roboflow
  ("YOLO YOGA Dataset").
- **v2** (15-20 lớp, Yoga-82 + pseudo-label): chỉ code stub, **không
  triển khai** — Giai đoạn 5 (feedback loop) không tìm ra lý do cần mở
  rộng dataset.
- Augmentation: `fliplr` bật, `flipud` tắt (lật dọc phá vỡ ý nghĩa tư
  thế yoga), `degrees` giới hạn (tránh xoay mạnh sai lệch tư thế).

---

## 4. Training & Ablation

- YOLOv8n, seed=42, epochs=50 (baseline).
- Ablation: augmentation ON vs OFF, cùng seed/epochs — ON thắng, chọn làm
  config chính thức.
- mAP@0.5 / mAP@0.5:0.95 thật: xem bảng trong `docs/problem_statement.md`
  mục "Training baseline".

---

## 5. Evaluation & Error Analysis

- Confusion matrix: không có cặp lớp nào bị nhầm đáng kể trong tập test
  (cùng phân bố với training).
- EigenCAM: model nhìn đúng vùng cơ thể, không bị phân tâm bởi nền (3-5
  ảnh minh hoạ trong notebook 03).
- → Đổi hướng "feedback loop": vì không có lỗi trong tập test, đo lỗi
  thật trên ảnh **ngoài phân bố** (OOD) thay vì sửa augmentation mù quáng.

---

## 6. Feedback loop — OOD test

- 18 ảnh thật ngoài dataset (Kaggle, khác nguồn hoàn toàn Roboflow).
- Kết quả: **17/18 = 94.4%** — 1 lỗi duy nhất khả năng do nhãn gốc dataset
  không chuẩn, không phải lỗi hệ thống.
- Kết luận: baseline đủ robust, **không retrain**.

---

## 7. Form scoring (ý tưởng riêng — rubric mục 6)

- MediaPipe Pose (pretrained) → 33 keypoint → góc khớp → so `POSE_RULES`
  (hiệu chỉnh bằng số đo thật trên 15 ảnh mẫu, ±15°).
- Kết quả: 14/15 ảnh mẫu đúng form + 5/5 case tổng hợp lệch góc phát hiện
  đúng.
- **2 hạn chế thật, ghi nhận công khai:** MediaPipe kém tin cậy trên tư
  thế lộn ngược (nền tương phản thấp); góc chiếu 2D bị méo khi camera
  chụp xiên (hạn chế cố hữu, không phải bug).

---

## 8. Export & Backend

- Export ONNX: nhanh hơn PyTorch ~17% (GPU T4 Colab: 206.29ms vs
  247.94ms).
- `app/service.py`: load model 1 lần (lazy), pipeline detect → crop →
  MediaPipe → score_pose() → JSON response.
- Test end-to-end thật (curl): đúng lớp, đúng form, latency CPU local
  ~245.8ms.

---

## 9. Web demo & Deploy public

- `web/index.html`: tab Upload ảnh + Camera trực tiếp, vẽ box/tip đè lên
  ảnh, card kết quả đọc được (không chỉ dump JSON thô).
- Deploy: **Render** (backend, free) + **Cloudflare Pages** (frontend,
  free) — 2 origin khác nhau, CORS siết đúng domain.
- Demo live: https://computer-vision-project.pthieu290998.workers.dev

---

## 10. Lỗi & bài học (chọn lọc từ toàn bộ quá trình)

- Bug so sánh tên lớp (tiền tố `"yoga-pose "`) làm OOD accuracy báo nhầm
  0% — sửa bằng đối chiếu log gốc, không đoán số liệu.
- `mediapipe>=1.0` bỏ hẳn API cũ (`solutions.pose`) — phải pin đúng
  `==0.10.21`, xác nhận thật qua lỗi build thật (không đoán trước).
- Deploy: 3 bug môi trường thật (Render chọn nhầm runtime Python thay vì
  Docker; thiếu `libGL.so.1` trên container Linux tối giản; iOS Safari
  đẩy camera vào native fullscreen player che overlay) — cả 3 đều chẩn
  đoán từ log/screenshot thật, không đoán mò, và đều verify lại được qua
  thiết bị/server thật sau khi sửa.

---

## 11. Demo

*(Quay video thật lúc trình bày — camera trực tiếp trên iPhone qua URL
public, upload ảnh, xem card kết quả + tip.)*

---

## Liên kết

- Repo: (điền link GitHub public)
- Demo live: https://computer-vision-project.pthieu290998.workers.dev
- Kiến trúc: `docs/architecture.md`
- Chi tiết đầy đủ 7 mục rubric: `docs/problem_statement.md`
