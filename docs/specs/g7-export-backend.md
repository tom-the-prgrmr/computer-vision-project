# Spec — g7. Export & Backend (rubric: mục 7 — Deployment)

**Plan source:** `docs/PLAN.md` — Giai đoạn 7
**Status:** implemented

## Mục tiêu

Export model detector tốt nhất sang ONNX, benchmark latency PyTorch vs
ONNX, và implement thật `app/service.py` (load ONNX 1 lần, detect + trích
landmark + chấm form qua `score_pose()` đã có từ Giai đoạn 6) để
`POST /predict` chạy được end-to-end.

**"Model tốt nhất" = `yolov8n_v1_baseline`** (config augmentation ON, chốt
ở Giai đoạn 3) — Giai đoạn 5 kết luận không cần retrain (OOD accuracy đã
94.4%, không có pattern lỗi để sửa), nên không có checkpoint "sau cải
tiến" nào khác để dùng.

## Việc cụ thể

Chia 2 phần độc lập: **(A)** cần checkpoint thật trên Colab/Drive — làm
qua notebook, bạn chạy thật; **(B)** code thuần, làm được toàn bộ trong
môi trường này, smoke-test bằng model chưa train (kỹ thuật đã dùng ở Giai
đoạn 4 cho EigenCAM — xác nhận code chạy đúng, không phải đo hiệu năng
thật).

### Phần A — `notebooks/04_export_onnx.ipynb` (Colab, bạn chạy thật)

**T7.1 — Export ONNX:**
- Thêm `src/models/export.py::export_onnx(model_path, imgsz=640, **kwargs) -> str`
  (wrapper mỏng quanh `YOLO(model_path).export(format="onnx", ...)`, cùng
  tinh thần `src/models/train.py::train()` — dùng lại được từ notebook lẫn
  chỗ khác).
- Notebook: load `runs/detect/yolov8n_v1_baseline/weights/best.pt`, gọi
  `export_onnx()`, xác nhận `best.onnx` tồn tại + `onnxruntime.InferenceSession`
  load được + 1 lần inference thử không lỗi.
- Copy `best.onnx` sang Google Drive (giống cách `best.pt` đã làm ở Giai
  đoạn 2) — cần cho benchmark T7.2 và để bạn tải về máy local dùng cho
  `app/` (env var `MODEL_PATH`, xem T7.4).

**T7.2 — Benchmark latency PyTorch vs ONNX:**
- N=50 lần inference (1 ảnh test cố định, lặp lại) qua `YOLO(...).predict()`
  (PyTorch) vs qua `src/models/onnx_inference.py` (phần B, cùng
  preprocess/postprocess dùng cho `app/service.py` — không viết code
  benchmark riêng, dùng lại đúng hàm production sẽ chạy).
- Bảng: avg latency (ms), FPS = 1000/latency, cho cả 2. Đo trên GPU T4
  Colab (không đại diện cho CPU thật lúc deploy — ghi rõ giới hạn này,
  không suy diễn số liệu CPU từ đây).

**T7.3 — Quantization (optional, chỉ làm nếu dư thời gian):** để nguyên
`[ ]` trong PLAN.md nếu bỏ qua, không bắt buộc.

### Phần B — `app/service.py` + `src/models/onnx_inference.py` (code, làm được ở đây)

**Thiết kế module mới `src/models/onnx_inference.py`** (logic `app/` cần,
đặt ở `src/` để notebook benchmark T7.2 dùng lại được, không lặp code —
theo `CLAUDE.md`):

```python
@dataclass
class RawDetection:
    class_id: int
    class_name: str
    confidence: float
    box: tuple[float, float, float, float]  # x1,y1,x2,y2, pixel space ẢNH GỐC

@dataclass
class LetterboxInfo:
    scale: float
    pad_x: float
    pad_y: float
    orig_w: int
    orig_h: int

def preprocess(image: np.ndarray, imgsz: int = 640) -> tuple[np.ndarray, LetterboxInfo]:
    """Letterbox resize (giữ tỉ lệ, pad màu (114,114,114) căn giữa —
    đúng quy ước Ultralytics) về (imgsz, imgsz), chuẩn hoá [0,1], HWC->CHW,
    thêm batch dim -> (1,3,imgsz,imgsz) float32. Trả kèm LetterboxInfo để
    postprocess() dịch ngược box về toạ độ ảnh gốc."""

def postprocess(
    raw_output: np.ndarray,  # (1, 4+nc, num_anchors) -- output thô ONNX, CHƯA NMS
    letterbox_info: LetterboxInfo,
    class_names: list[str],
    conf_threshold: float,
    iou_threshold: float = 0.45,
) -> list[RawDetection]:
    """Transpose (num_anchors, 4+nc) -> lọc theo max-class-score > conf_threshold
    -> NMS THEO TỪNG LỚP RIÊNG (cv2.dnn.NMSBoxes mỗi class_id -- không NMS
    gộp chung, vì 2 học viên khác tư thế có thể chồng box thật, không nên
    bị NMS gộp lớp xoá nhầm) -> dịch box từ toạ độ letterbox về ảnh gốc
    (trừ pad, chia scale, clip theo orig_w/orig_h) -> list[RawDetection].
    Output ONNX YOLOv8 mặc định (export KHÔNG kèm NMS, không có cột
    "objectness" riêng như YOLOv5 -- cột 4: đã là class scores post-sigmoid
    trực tiếp) -- confidence = max class score, class_id = argmax.

    class_names PHẢI truyền tay đúng thứ tự train (không đọc từ metadata
    ONNX -- không đáng tin cậy/không nhất quán giữa các bản export), và
    PHẢI đã bỏ tiền tố "yoga-pose " (xem bug thật đã gặp ở Giai đoạn 5,
    docs/specs/g5-feedback-loop.md) -- mặc định
    ["bridge","downward","plank","shoulderstand","tree"] đúng thứ tự index
    trong data.yaml.

    Không hardcode nc=5 trong toán học (chỉ dùng class_names cho việc đặt
    tên) -- để smoke-test được với model chưa train (nc khác) mà không
    phải sửa code.
    """

def run_onnx_detection(
    session: onnxruntime.InferenceSession,
    image: np.ndarray,  # RGB, HWC
    class_names: list[str],
    conf_threshold: float,
    imgsz: int = 640,
) -> list[RawDetection]:
    """preprocess -> session.run() -> postprocess, gộp lại thành 1 lời gọi
    duy nhất cho app/service.py::_detect() lẫn notebook benchmark T7.2."""
```

**T7.4 — `app/service.py::_ensure_loaded()`:**
```python
self._session = onnxruntime.InferenceSession(self.model_path, providers=["CPUExecutionProvider"])
self._pose = new_pose_model()  # src/pose_scoring/landmark_extraction.py, Giai đoạn 6 đã có sẵn
```
`self._session is not None and self._pose is not None` (guard đã có sẵn
trong stub) giữ nguyên -- chỉ cần gán 2 dòng trên.

**T7.5 — `_detect()` + `_extract_landmarks()`:**
- `_detect(image)`: `return run_onnx_detection(self._session, image, self.class_names, self.conf_threshold)`.
  `PoseDetectionService.__init__` thêm tham số
  `class_names: list[str] = ["bridge","downward","plank","shoulderstand","tree"]`
  (không đọc từ file ONNX — lý do ở trên).
- `_extract_landmarks(crop)`: gọi `extract_landmarks_px(crop, self._pose)`
  (Giai đoạn 6, `src/pose_scoring/landmark_extraction.py`).
  **Sửa 1 bug thật phát hiện khi thiết kế phần này:** `extract_landmarks_px()`
  hiện giả định input BGR (gọi `cv2.cvtColor(image, COLOR_BGR2RGB)` bên
  trong, đúng cho `cv2.imread()` ở Giai đoạn 6's scripts) -- nhưng
  `app/service.py::predict_image()` load ảnh qua PIL
  (`Image.open(...).convert("RGB")`), `crop` đã là **RGB sẵn**. Gọi thẳng
  hàm cũ sẽ đảo nhầm kênh R/B. Sửa: đổi contract `extract_landmarks_px()`
  nhận **RGB trực tiếp** (bỏ `cv2.cvtColor` bên trong -- MediaPipe
  `pose.process()` vốn cần RGB, không cần BGR trung gian), cập nhật 2 chỗ
  gọi cũ ở `scripts/calibrate_pose_rules.py` và
  `scripts/manual_test_score_pose.py` tự `cv2.cvtColor(BGR2RGB)` trước khi
  gọi (chúng dùng `cv2.imread()` nên có BGR).

**T7.6 — Test bằng `curl`:** giữ nguyên route `POST /predict` đã wire sẵn
ở `app/controller.py`, không cần sửa.

**T7.7 — `/predict_video` (optional):** để `NotImplementedError`, không
làm trừ khi dư thời gian (đúng note đã có sẵn trong code).

## File/module liên quan

- `src/models/export.py` (mới)
- `src/models/onnx_inference.py` (mới)
- `src/pose_scoring/landmark_extraction.py` (sửa contract BGR->RGB)
- `scripts/calibrate_pose_rules.py`, `scripts/manual_test_score_pose.py` (sửa theo contract mới)
- `app/service.py` (implement `_ensure_loaded`, `_detect`, `_extract_landmarks`, thêm `class_names` param)
- `notebooks/04_export_onnx.ipynb` (mới)

## Bằng chứng / số liệu kỳ vọng

- Phần A (bạn chạy Colab): `best.onnx` tồn tại + load được; bảng latency
  PyTorch vs ONNX thật (avg ms, FPS)
- Phần B (làm ở đây): smoke test `TestClient` gọi `/predict` với 1 ảnh
  giả qua model **chưa train** (`YOLO('yolov8n.yaml').export(format='onnx')`,
  kỹ thuật như Giai đoạn 4) — xác nhận không crash, response đúng schema
  `PredictResponse`, không phải đo độ chính xác (model chưa train ra
  detection vô nghĩa, chỉ cần *chạy được hết pipeline*)

## Cách bạn tự test sau khi tôi xong

1. Trên Colab: chạy `notebooks/04_export_onnx.ipynb` (Setup → git pull →
   T7.1 export → T7.2 benchmark), báo lại bảng latency thật.
2. Tải `best.onnx` về máy (từ Drive), đặt vào `models/best.onnx`
   (hoặc set env var `MODEL_PATH` trỏ tới đó).
3. Local: `uvicorn app.main:app --reload`, rồi:
   ```bash
   curl -F "image=@sample.jpg" http://localhost:8000/predict
   ```
   (dùng 1 ảnh yoga thật bất kỳ, vd 1 ảnh trong `data/pose_rule_samples/`).
   Kiểm tra response có `detections` với `pose`/`confidence`/`box`/`form_ok`/`tips`.

## ❓ Quyết định cần bạn chốt

Không có — "model tốt nhất" đã rõ (baseline, do Giai đoạn 5 không
retrain), thiết kế postprocess/NMS/letterbox theo đúng quy ước chuẩn
YOLOv8 ONNX export, không có tham số nào cần bạn tự chọn.

## Rủi ro / điều cần lưu ý

- Benchmark T7.2 đo trên GPU Colab (T4), không đại diện cho CPU thật lúc
  deploy (Giai đoạn 9 dùng Hugging Face Spaces CPU free-tier theo
  `PLAN.md`) — sẽ ghi rõ giới hạn này trong kết luận, không suy diễn số
  liệu CPU từ đây.
- NMS theo từng lớp riêng (không gộp) có thể chậm hơn 1 chút với nhiều
  lớp/nhiều box, nhưng đúng hơn về mặt semantics (nhiều học viên khác tư
  thế trong khung không nên bị NMS gộp lớp xoá nhầm) — chấp nhận đánh đổi
  này, không tối ưu tốc độ ở bước này.
- Smoke test phần B dùng model **chưa train** — không chứng minh detection
  thật đúng, chỉ chứng minh pipeline code chạy hết không crash. Độ chính
  xác thật chỉ xác nhận được khi bạn tự `curl` với `best.onnx` thật (bước
  3 ở "Cách bạn tự test").
- `iou_threshold=0.45` là giá trị mặc định phổ biến của Ultralytics, không
  tự tinh chỉnh riêng cho dataset này (ngoài phạm vi rubric mục 7).

## Implementation notes

**Files touched:** `src/models/onnx_inference.py`, `src/models/export.py`
(mới), `app/service.py` (implement `_ensure_loaded`/`_detect`/`_extract_landmarks`,
thêm `class_names` param), `src/pose_scoring/landmark_extraction.py` (đổi
contract BGR->RGB), `scripts/calibrate_pose_rules.py`,
`scripts/manual_test_score_pose.py` (cập nhật theo contract mới),
`notebooks/04_export_onnx.ipynb` (mới).

**Phần B (code, đã làm xong ở đây):** implement đúng thiết kế trong spec.
Review + smoke test bắt được 3 vấn đề thật, đã sửa hết:

1. `cv-architecture-review` lượt 1: `postprocess()` có thể `IndexError`
   nếu số lớp model ONNX ≠ `len(class_names)` (vd model chưa train nc=80
   nhưng `class_names` mặc định chỉ 5 phần tử) — thêm validate + lỗi rõ
   ràng thay vì crash mập mờ. Lượt 2: sạch.
2. `code-review` (medium): lỗi làm tròn pad letterbox — `preprocess()`
   đặt ảnh lên canvas theo pad đã `round()`, nhưng lưu lại pad **chưa
   round** vào `LetterboxInfo`, khiến `postprocess()` dịch box ngược lệch
   tới ~0.5px/scale khi `(imgsz - new_w)` hoặc `(imgsz - new_h)` là số lẻ
   (ảnh tỉ lệ khung hình lệch mạnh, vd 100×3000). Sửa: round pad 1 lần
   duy nhất, dùng thống nhất cho cả đặt ảnh lẫn `LetterboxInfo`. Verify
   bằng test round-trip tay với case 100×3000 (trước: lệch ~2.3px, sau:
   lệch 0).
3. Bug thật khác (không phải finding từ review, phát hiện lúc thiết kế):
   `extract_landmarks_px()` cũ giả định input BGR, nhưng
   `app/service.py` dùng PIL (RGB) — nếu gọi thẳng sẽ đảo nhầm kênh R/B.
   Đổi contract nhận RGB trực tiếp, cập nhật 2 script Giai đoạn 6 tự
   convert BGR->RGB trước khi gọi.

**Smoke test:** FastAPI `TestClient` gọi `POST /predict` thật qua model
**chưa train** (`YOLO('yolov8n.yaml').export(format='onnx')`, nc=80 mặc
định COCO — kỹ thuật như Giai đoạn 4) với `conf_threshold` hạ cực thấp để
ép có detection (weight ngẫu nhiên cho class score tối đa chỉ ~1.5e-4 sau
sigmoid) — xác nhận **373 detection** đi hết pipeline (ONNX detect → crop
→ MediaPipe → `score_pose()`) không crash, response đúng schema
`PredictResponse`, `/health` vẫn hoạt động. Không đo được độ chính xác
thật (model chưa train) — chỉ xác nhận code chạy đúng.

**T7.1/T7.2 — chạy thật trên Colab (kết quả thật):** export ONNX thành
công (`best.onnx`), xác nhận `onnxruntime` load + inference được. Benchmark
N=50, GPU T4: PyTorch (.pt) 247.94ms/4.03fps, ONNX Runtime (.onnx)
206.29ms/4.85fps — ONNX nhanh hơn ~17%. Ghi vào `problem_statement.md` +
`notebooks/04_export_onnx.ipynb`.

**Sự cố môi trường thật gặp khi chạy (đã sửa):**
`requirements.txt` pin `mediapipe==0.10.21` (chốt theo bản có sẵn trên máy
Windows local) không có wheel cho Python trên Colab — chỉ `0.10.30+`/`1.0.x`
khả dụng ở đó, khiến `pip install -r requirements.txt` thất bại hoàn toàn
(không chỉ riêng mediapipe). Sửa: nới thành khoảng `mediapipe>=0.10,<1.0`
— toàn bộ dòng `0.10.x` (gồm `0.10.30+`) vẫn còn API cũ `solutions.pose`
(chỉ `1.0+` mới bỏ, xem Giai đoạn 6), nên khoảng này portable qua nhiều
Python/platform mà vẫn tránh được bug gốc.

T7.3 (quantization) và T7.7 (`/predict_video`) là optional, không làm
(đúng buffer priority trong PLAN.md).

**T7.6 — `curl` thật (kết quả thật, CPU local, `best.onnx` thật đã tải
về `models/best.onnx`):**
```json
{"detections":[{"pose":"tree","confidence":0.92,"box":[256.2,73.5,449.1,592.7],
  "form_ok":true,"tips":[],"latency_ms":245.8}]}
```
Đúng lớp, confidence cao, `form_ok=true` — xác nhận toàn bộ pipeline thật
(ONNX detect → crop → MediaPipe → `score_pose()`) chạy đúng end-to-end,
không chỉ smoke test model giả nữa.
