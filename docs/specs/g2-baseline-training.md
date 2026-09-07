# Spec — G2. Baseline training (rubric: mục 3 — Huấn luyện)

**Plan source:** `docs/PLAN.md` — Giai đoạn 2 (`T2.1`–`T2.5`)
**Status:** implemented

## Mục tiêu

Train baseline YOLOv8 detector trên dataset v1 (5 lớp, 1013 ảnh — số liệu
thật từ `docs/specs/g1-data.md`), dùng chung 1 wrapper `train()` tái sử dụng
được ở cả Giai đoạn 3 (ablation) và Giai đoạn 5 (retrain sau cải tiến), và
ghi lại mAP@0.5 / mAP@0.5:0.95 baseline làm mốc so sánh cho các bước sau.

## Việc cụ thể

- **T2.1 — `train()` trong `src/models/train.py`**
  Wrapper thin quanh `ultralytics.YOLO(model).train(...)`, cố định các
  tham số cần cho reproducibility (`seed`) và augmentation đã chốt ở T1.5
  (`flipud=0.0, fliplr=0.5, degrees=10`) làm default, cho phép override qua
  `**kwargs` để Giai đoạn 3 (ablation on/off) và Giai đoạn 5 (retrain) gọi
  lại được mà không copy-paste hyperparameter.
  Chữ ký: `train(data: str, model: str = "yolov8n.pt", epochs: int = 50,
  seed: int = 42, imgsz: int = 640, flipud: float = 0.0, fliplr: float =
  0.5, degrees: float = 10.0, **kwargs) -> DetMetrics` (trả về
  `DetMetrics` — kết quả validate cuối cùng mà `YOLO.train()` tự chạy trên
  `best.pt`; có `.save_dir`, `.box.map50`, `.box.map`).
  Acceptance: import được (`from src.models.train import train`), chữ ký +
  default khớp mô tả trên. Hàm gọi `YOLO(model)` ngay dòng đầu (không có
  bước "dựng tham số" tách riêng trước đó), nên test cú pháp thật sự chỉ ở
  mức import + kiểm tra signature — muốn test sâu hơn (thật sự gọi
  `train(...)`) cần `ultralytics` cài + mạng (tải checkpoint) + dữ liệu,
  xem "Cách bạn tự test".

- **T2.2 — Gọi từ notebook**
  `notebooks/02_train_detector.ipynb`, cell gọi `train(data="data/raw/
  yoga_v1/data.yaml", model="yolov8n.pt", seed=42, epochs=50)`.
  **Epochs = 50** (chốt, không còn "vd"): đủ để `yolov8n` hội tụ trên
  ~1013 ảnh/5 lớp trong 1 session Colab free T4 (ước tính vài chục phút),
  vẫn để dư giờ session cho Giai đoạn 3 (train thêm 1 lần ablation) trong
  cùng ngày — xem ràng buộc compute ở `docs/REQUIREMENTS.md` mục 5.
  `imgsz=640` (mặc định Ultralytics, ảnh dataset đủ lớn, không cần đổi).
  `batch` để mặc định của Ultralytics (không ép cứng — tuỳ VRAM T4 lúc
  chạy).
  Acceptance: cell chạy xong không lỗi, in ra `results.save_dir`.

- **T2.3 — Xác nhận output**
  Sau khi train, in đường dẫn `results.save_dir` và liệt kê file trong đó
  (`results.csv`, `results.png`, `weights/best.pt`, `weights/last.pt`).
  Acceptance: notebook in ra danh sách file, xác nhận cả 4 file trên tồn
  tại.

- **T2.4 — Weights vào Drive**
  Vì notebook đã `cd` vào thư mục repo **trong Drive** ngay từ đầu (cell
  "Setup — mount Drive + cd vào repo", thêm ở Giai đoạn 1) nên
  `runs/detect/.../weights/best.pt` **tự động nằm trong Drive** — không
  cần bước copy thủ công riêng như PLAN.md dự tính ban đầu (lúc đó giả
  định notebook chạy ở `/content` cục bộ). Chỉ cần xác nhận đường dẫn
  `results.save_dir` bắt đầu bằng `/content/drive/...`.
  Acceptance: cell in `results.save_dir`, xác nhận prefix `/content/drive/`
  (trên Colab) — nếu không đúng, nghĩa là cell setup Giai đoạn 1 chưa chạy
  trước.

- **T2.5 — Ghi mAP baseline**
  `train()` tự chạy validate trên `best.pt` ở cuối training rồi trả về
  `DetMetrics` đó — đọc `results.box.map50` / `results.box.map` trực tiếp
  từ object đã có ở T2.1-T2.2, **không** load lại checkpoint + gọi `.val()`
  thêm lần nữa (tốn thời gian session free-tier vô ích). In ra, rồi
  markdown cell điền số liệu thật (giống pattern T1.6 — không bịa số, chờ
  chạy thật trên Colab).
  Acceptance: markdown cell có 2 số liệu thật (mAP@0.5, mAP@0.5:0.95) sau
  khi người dùng chạy xong và cung cấp lại.

## File/module liên quan

- `src/models/train.py` — **mới**, implement thật (không phải stub) vì đây
  chỉ là 1 wrapper mỏng, không có phần nào cần thiết kế thêm.
- `notebooks/02_train_detector.ipynb` — **mới**, theo đúng pattern
  notebook 01 (mount Drive + cd + cài deps ở đầu, tái dùng nguyên cell đó).
- `docs/problem_statement.md` — chưa cần sửa ở bước này (mAP baseline ghi
  vào notebook trước, đưa vào docs khi có bảng so sánh ở Giai đoạn 3/5,
  tránh ghi 2 lần).

## Bằng chứng / số liệu kỳ vọng

- `runs/detect/<name>/results.csv` + `results.png` (loss/mAP theo epoch) — có.
- `runs/detect/<name>/weights/best.pt` tồn tại, nằm trong Drive — có.
- mAP@0.5 = **0.9923**, mAP@0.5:0.95 = **0.8435** (số thật, chạy trên Colab
  T4, `yolov8n.pt`, 50 epochs, seed=42).

## Cách bạn tự test sau khi tôi xong

1. Mở `notebooks/02_train_detector.ipynb` trên Colab (cùng repo đã clone ở
   T0.4) — cell đầu (mount Drive + cd + cài deps) giống hệt notebook 01,
   chạy trước tiên.
2. Chạy cell gọi `train(...)` — sẽ mất khoảng vài chục phút trên T4 free
   (50 epochs, `yolov8n`, ~1013 ảnh). Theo dõi tab Colab đừng để session
   ngủ (giữ tab active).
3. Chạy các cell còn lại (T2.3–T2.5) để xem `results.save_dir`, danh sách
   file, và mAP cuối cùng.
4. Gửi lại mAP@0.5 / mAP@0.5:0.95 cho mình để ghi vào notebook markdown
   cell (và làm mốc so sánh khi viết docs ở Giai đoạn 3/5).

## ❓ Quyết định cần bạn chốt

Không có quyết định mơ hồ — epochs (50), model (`yolov8n.pt`), seed (42),
imgsz (640) đã chốt cụ thể ở trên dựa trên PLAN.md + ràng buộc compute
free-tier đã biết trước. Nếu 50 epochs chạy xong mà loss/mAP rõ ràng chưa
hội tụ (vẫn giảm mạnh ở epoch cuối), có thể cần bàn lại tăng epochs — nhưng
đó là quyết định *sau khi* thấy kết quả thật, không phải bây giờ.

## Rủi ro / điều cần lưu ý

- Không thể test training thật trong môi trường CLI này (không có
  `ultralytics` cài, không có GPU) — smoke test chỉ ở mức cú pháp/import,
  xem "Cách bạn tự test" để có kết quả thật.
- Colab free T4 có giới hạn giờ/session — nếu bị ngắt giữa chừng, Ultralytics
  tự resume được từ `last.pt` (`model.train(resume=True)`) nhưng không nằm
  trong scope wrapper `train()` mặc định; xử lý riêng nếu gặp phải.
- `POSE_RULES` trong `angle_rules.py` hiện dùng tên lớp mẫu (`tree`,
  `warrior2`) không khớp 5 lớp thật của v1 (`bridge`, `downward`, `plank`,
  `shoulderstand`, `tree`) — không phải việc của Giai đoạn 2, nhưng cần
  nhớ sửa ở Giai đoạn 6 (T6.1+).

## Implementation notes

- **T2.1 — done.** `src/models/train.py` — wrapper thật (không stub),
  chữ ký `train(data, model="yolov8n.pt", epochs=50, seed=42, imgsz=640,
  flipud=0.0, fliplr=0.5, degrees=10.0, **kwargs) -> DetMetrics`, augmentation
  khớp T1.5. Đã tạo `.venv` local + `pip install -r requirements.txt`
  (theo yêu cầu của người dùng) để smoke-test import thật thay vì chỉ
  syntax-check suông.
  - Review: `cv-architecture-review` 2 lần + `code-review` (medium).
    4 finding từ lần review đầu, tất cả đã sửa:
    1. Type hint sai (`Results` thay vì `DetMetrics` — đúng type
       `YOLO.train()` thực sự trả về) → sửa import + annotation +
       docstring trong `train.py`.
    2. Notebook cell T2.5 load lại checkpoint + gọi `.val()` thêm 1 lần dù
       `results` (từ T2.1-T2.2) đã có sẵn `DetMetrics` — tốn thời gian
       session Colab free-tier vô ích → sửa cell dùng thẳng
       `results.box.map50`/`results.box.map`.
    3. Spec T2.1 acceptance mô tả 1 bước "dựng tham số trước khi gọi
       `YOLO(...)`" không khớp code thật (gọi `YOLO(model)` ngay dòng đầu)
       → sửa lại acceptance cho khớp.
    4. `README.md` claim `python -m src.models.train` chạy được như CLI —
       sai, `train.py` không có entrypoint CLI → sửa README chỉ còn nhắc
       tới notebook.
    Lần review thứ 2 xác nhận sạch cả 4 fix + không phát sinh finding mới.
  - Smoke test (trong `.venv`, package thật): `from src.models.train
    import train` thành công, `inspect.signature(train)` khớp mô tả spec;
    `python -m py_compile` qua `train.py` + các file `app/` liên quan;
    JSON + cú pháp Python của cả 2 notebook (`01`, `02`) hợp lệ. Không gọi
    `train(...)` thật (cần network tải checkpoint + GPU + dataset — ngoài
    phạm vi CLI này).
- **T2.2-T2.5 — done.** Chạy thật trên Colab (T4 GPU), `yolov8n.pt`,
  `seed=42`, `epochs=50`. Kết quả: **mAP@0.5 = 0.9923, mAP@0.5:0.95 =
  0.8435** — rất cao cho baseline, dataset v1 tương đối "dễ" (5 lớp phân
  biệt rõ về hình dạng tư thế, học viên thường chiếm phần lớn khung hình).
  Ghi vào markdown cell cuối `notebooks/02_train_detector.ipynb`. `results.
  save_dir` xác nhận nằm trong Drive (`/content/drive/...`), `results.csv`/
  `results.png`/`weights/{best,last}.pt` đều tồn tại.

  Lưu ý phát sinh lúc chạy (không phải lỗi, chỉ perf warning): Ultralytics
  cảnh báo "Slow image access" vì đọc ảnh từ Drive (mounted, chậm hơn đĩa
  local Colab) — không chặn training, chỉ là đánh đổi đã chọn ở Giai đoạn 1
  (train trong Drive để không mất `best.pt` khi hết session). Không cần xử
  lý; có thể thêm `cache=True` vào lần gọi `train()` sau nếu muốn train
  nhanh hơn (cache ảnh vào RAM sau lần đọc đầu).

**Giai đoạn 2 hoàn tất** — tất cả T2.1–T2.5 đã tick trong `docs/PLAN.md`.
mAP baseline dùng làm mốc so sánh cho Giai đoạn 3 (ablation) và Giai đoạn 5
(feedback loop retrain).
