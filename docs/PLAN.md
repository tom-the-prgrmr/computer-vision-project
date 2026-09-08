# Kế hoạch triển khai

Deadline: **15/9**. Hôm nay: **28/8** → còn 18 ngày. Ưu tiên tuyệt đối:
**pipeline v1 (5 lớp) chạy hết vòng đời trước**, mọi thứ optional (v2, GPU
thuê, quantization) chỉ đụng tới nếu còn dư thời gian — đúng tinh thần
`docs/REQUIREMENTS.md` mục 8 (Out of scope).

Mỗi task có mã `T<giai đoạn>.<số>`, đủ nhỏ để làm trong 1 buổi. Làm tuần tự
trong 1 giai đoạn trừ khi ghi "song song". Nếu trễ tiến độ, cắt theo thứ tự ở
mục Buffer cuối file — không cắt vào 7 mục bắt buộc.

## Giai đoạn 0 — Setup (28/8)
- [x] T0.1 `git diff` review lại thay đổi hiện tại, commit, push lên `origin/main`
- [x] T0.2 Tạo Roboflow account / lấy API key, điền vào `.env` local (theo mẫu `.env.example`, **không** commit `.env`)
- [x] T0.3 Mở Colab, thêm Colab Secret `ROBOFLOW_API_KEY`
- [x] T0.4 Mount Google Drive, `git clone` repo vào Drive (để checkpoint không mất khi hết session)
- [x] T0.5 `pip install -r requirements.txt` trong Colab, xác nhận `ultralytics`/`mediapipe` import được

## Giai đoạn 1 — Data (29/8 – 30/8)
File: `scripts/download_data.sh`, `notebooks/01_data_exploration.ipynb`
- [x] T1.1 Chạy `scripts/download_data.sh` (hoặc gọi trực tiếp Roboflow Python API trong notebook) → xác nhận `data/raw/yoga_v1/{train,valid,test}` + `data.yaml` tồn tại
- [x] T1.2 Load `data.yaml`, in số lớp + số ảnh mỗi split
- [x] T1.3 Vẽ biểu đồ phân bố ảnh theo lớp (kiểm tra imbalance)
- [x] T1.4 Vẽ bbox lên 2-3 ảnh mẫu mỗi lớp để sanity-check nhãn đúng
- [x] T1.5 Chốt augmentation: tắt `flipud`, giữ `fliplr`, giới hạn `degrees` (tránh xoay mạnh sai lệch tư thế) — ghi cụ thể giá trị dùng
- [x] T1.6 Ghi kết quả (nguồn, số lượng, split, imbalance, augmentation + lý do) vào mục "Data" của `docs/problem_statement.md`

## Giai đoạn 2 — Baseline training (31/8 – 1/9)
File: `src/models/train.py`, `notebooks/02_train_detector.ipynb`
- [x] T2.1 Viết `train()` trong `src/models/train.py`: wrapper quanh `ultralytics.YOLO(model).train(data=..., epochs=..., seed=..., **kwargs)`
- [x] T2.2 Gọi từ notebook với `model="yolov8n.pt"`, `seed=42`, epochs baseline (vd 50)
- [x] T2.3 Xác nhận `results.csv`/`results.png` (loss/mAP theo epoch) được lưu ở `runs/detect/...`
- [x] T2.4 Copy `weights/best.pt` sang Google Drive để không mất khi hết session
- [x] T2.5 Ghi mAP@0.5, mAP@0.5:0.95 baseline vào markdown cell trong notebook

## Giai đoạn 3 — Ablation (2/9 – 3/9)
- [x] T3.1 Chọn biến ablation: **augmentation on vs off** (rẻ nhất, chạy 2 lần là đủ)
- [x] T3.2 Train variant thứ 2, giữ nguyên seed/epochs/model, chỉ đổi biến đã chọn
- [x] T3.3 Lập bảng so sánh baseline vs variant (mAP, thời gian train) trong notebook
- [x] T3.4 Chọn config thắng làm "chính thức", ghi lý do vào `docs/problem_statement.md`

## Giai đoạn 4 — Evaluation & Error Analysis (4/9 – 5/9)
File: `src/evaluation/metrics.py`, `notebooks/03_evaluation_error_analysis.ipynb`
- [x] T4.1 Viết helper trong `metrics.py` để load/hiển thị confusion matrix từ kết quả validate của Ultralytics
- [x] T4.2 Xác định 2-3 cặp lớp hay bị nhầm nhất từ confusion matrix
- [x] T4.3 Cài `pytorch-grad-cam`, chạy **EigenCAM** (không dùng Grad-CAM chuẩn — xem lý do trong `REQUIREMENTS.md` mục 7) trên model đã train, chọn target layer ở cuối backbone
- [x] T4.4 Lưu 3-5 ảnh EigenCAM kèm 1-2 câu giải thích mỗi ảnh (model nhìn đúng chỗ hay bị phân tâm bởi nền?)
- [x] T4.5 Viết tóm tắt pattern lỗi (vd: sai nhiều khi vật nhỏ/bị che khuất/ánh sáng yếu/2 tư thế dáng giống nhau) vào notebook

## Giai đoạn 5 — Feedback loop cải tiến (6/9 – 8/9)
- [x] T5.1 Từ T4.2/T4.5, chọn 1 hướng cải thiện cụ thể — mặc định: augmentation/oversampling nhắm đúng cặp lớp hay nhầm (an toàn thời gian); chỉ làm v2 (`src/data/bootstrap_bbox.py`, mở rộng 15-20 lớp) nếu **đã xong T5.1-T5.4 sớm và còn dư thời gian**
- [ ] T5.2 Implement thay đổi (sửa config augment, hoặc nếu làm v2 thì chạy `bootstrap_bboxes()`)
- [ ] T5.3 Retrain với cùng seed, lưu thành run mới (không ghi đè run cũ — cần cả 2 để so sánh)
- [ ] T5.4 Lập bảng trước/sau: mAP tổng + mAP riêng cho (các) lớp đã cải thiện
- [ ] T5.5 Viết kết luận vào `docs/problem_statement.md`, đánh dấu mục 5 trong `docs/requirement_checklist.md`

## Giai đoạn 6 — Form scoring rule-based (6/9 – 8/9, song song GĐ5)
File: `src/pose_scoring/angle_rules.py`
- [ ] T6.1 Thu thập 2-3 ảnh/frame "form đúng" mỗi tư thế (tự chụp hoặc chọn lọc từ dataset)
- [ ] T6.2 Chạy MediaPipe Pose trên ảnh mẫu, in góc khớp thật ra để hiệu chỉnh `min_deg`/`max_deg` trong `POSE_RULES` (thay placeholder hiện tại)
- [ ] T6.3 Implement `score_pose()`: với mỗi `AngleRange` của `POSE_RULES[pose_class]`, tính góc qua `joint_angle()`, so ngưỡng, gom `issues`
- [ ] T6.4 Test thủ công: chạy `score_pose()` trên 2 ảnh đúng + 2 ảnh sai mỗi tư thế, xác nhận output hợp lý bằng mắt
- [ ] T6.5 Xử lý pose ngoài `POSE_RULES` (chưa hiệu chỉnh) — trả `ok=True`, `issues=[]` thay vì crash

## Giai đoạn 7 — Export & Backend (9/9 – 10/9)
File: `notebooks/04_export_onnx.ipynb`, `app/service.py`, `app/controller.py`
- [ ] T7.1 `model.export(format="onnx")` trên model tốt nhất (từ GĐ5), xác nhận file `.onnx` chạy được
- [ ] T7.2 Benchmark latency: N lần inference PyTorch `.pt` vs ONNX Runtime `.onnx`, lập bảng avg latency/FPS
- [ ] T7.3 *(optional, cần dư thời gian/GPU thuê)* thử dynamic quantization ONNX, benchmark lại
- [ ] T7.4 `app/service.py`: implement `_ensure_loaded()`/`_detect()` — load `onnxruntime.InferenceSession` 1 lần (lazy, không load lại mỗi request)
- [ ] T7.5 Implement `_extract_landmarks()` (MediaPipe) trong `app/service.py`; `/predict` ở `app/controller.py` chỉ cần gọi `service.predict_image()` — đã wire sẵn
- [ ] T7.6 Test bằng `curl -F "image=@sample.jpg" localhost:8000/predict`, kiểm tra response khớp schema
- [ ] T7.7 *(optional)* implement `/predict_video`

## Giai đoạn 8 — Web demo local (11/9)
File: `web/index.html`
- [ ] T8.1 `uvicorn app.main:app --reload`
- [ ] T8.2 Test tab "Upload ảnh" với API thật
- [ ] T8.3 Test tab "Camera trực tiếp" trên webcam máy dev qua `localhost` (không cần HTTPS ở bước này)
- [ ] T8.4 Fix lỗi lệch toạ độ overlay canvas vs kích thước video hiển thị nếu có (lỗi thường gặp)

## Giai đoạn 9 — Deploy public (12/9)
- [ ] T9.1 Chốt host — **mặc định: Hugging Face Spaces (Docker Space)**, free tier, có HTTPS sẵn (giải quyết luôn ràng buộc HTTPS cho camera iPhone ở §7 REQUIREMENTS, khỏi tự set up Caddy/Let's Encrypt); CPU đủ cho ONNX Runtime ở mức demo. Chỉ đổi sang VM GPU thuê + Caddy nếu latency CPU không chấp nhận được
- [ ] T9.1b *(optional)* Upload `best.onnx` lên Hugging Face Hub — link tải public gọn hơn cho README, thay vì xin quyền Google Drive
- [ ] T9.2 Set up HTTPS thật (bỏ qua nếu dùng HF Spaces — đã có sẵn)
- [ ] T9.3 Sửa `API_BASE` trong `web/index.html`, siết `allow_origins` trong `app/main.py` về đúng domain frontend
- [ ] T9.4 Deploy backend + serve `web/index.html`
- [ ] T9.5 Test camera trên **iPhone thật** qua URL HTTPS công khai — đây là điều kiện để coi FR7 hoàn thành

## Giai đoạn 10 — Tài liệu & Slide (13/9 – 14/9)
- [ ] T10.1 Viết lại README với kết quả/số liệu thật (không còn "đang thiết kế")
- [ ] T10.2 Vẽ sơ đồ kiến trúc model + luồng xử lý end-to-end (mermaid hoặc excalidraw, lưu vào `docs/`)
- [ ] T10.3 Điền đầy đủ `docs/problem_statement.md` bằng số liệu/kết quả thật thay vì kế hoạch
- [ ] T10.4 Làm slide tóm tắt (`docs/slides/`)
- [ ] T10.5 Đánh dấu hết các mục trong `docs/requirement_checklist.md`

## Giai đoạn 11 — Video & nộp bài (15/9)
- [ ] T11.1 Viết outline video: bài toán → dữ liệu → cách làm → kết quả → lỗi & bài học → demo chạy thật
- [ ] T11.2 Quay (ưu tiên quay demo camera trực tiếp thật trên điện thoại)
- [ ] T11.3 Edit, xuất video 5-10 phút
- [ ] T11.4 Push lần cuối lên GitHub, xác nhận repo public
- [ ] T11.5 Nộp trên Google Classroom kèm link GitHub

## Buffer — nếu trễ, cắt theo thứ tự này
1. v2 mở rộng lớp (T5.1 nhánh v2)
2. Quantization + benchmark sâu (T7.3)
3. `/predict_video` (T7.7)
4. Diagram đẹp (T10.2) → thay bằng ASCII/mermaid đơn giản có sẵn trong `README.md`
