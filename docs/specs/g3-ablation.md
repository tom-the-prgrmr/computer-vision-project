# Spec — G3. Ablation (rubric: mục 3 — Method & Training, phần "≥1 ablation")

**Plan source:** `docs/PLAN.md` — Giai đoạn 3 (`T3.1`–`T3.4`)
**Status:** implemented <!-- code xong — chạy thật trên Colab + T3.4 kết luận còn deferred, xem Implementation notes -->

## Mục tiêu

Chạy đúng "1 ablation" mà rubric mục 3 yêu cầu (`docs/requirement_checklist.md`
dòng 14: "≥1 ablation (biến đổi 1 yếu tố, seed cố định)") — biến đổi
**augmentation** (on vs off), giữ nguyên `model`/`seed`/`epochs`/`imgsz`,
lập bảng so sánh baseline (đã có số thật ở Giai đoạn 2) với variant, và
chốt config nào dùng chính thức cho các bước sau (Giai đoạn 5 retrain, ...).

## Việc cụ thể

- **T3.1 — Chốt biến ablation: augmentation ON vs OFF**
  Đã chọn sẵn trong PLAN.md ("rẻ nhất, chạy 2 lần là đủ"). Định nghĩa cụ
  thể (spec này chốt, không để notebook tự đoán):
  - **ON** = chính config baseline Giai đoạn 2 (mặc định `train()`:
    `flipud=0.0, fliplr=0.5, degrees=10.0`, mọi augmentation khác — mosaic,
    hsv, translate, scale, shear, perspective, mixup, copy_paste, erasing —
    giữ **mặc định của Ultralytics** vì đó là những gì baseline đã chạy).
  - **OFF** = tắt toàn bộ augmentation (không chỉ 3 tham số T1.5): gọi
    `train(..., flipud=0.0, fliplr=0.0, degrees=0.0, translate=0.0,
    scale=0.0, shear=0.0, perspective=0.0, hsv_h=0.0, hsv_s=0.0, hsv_v=0.0,
    mosaic=0.0, mixup=0.0, copy_paste=0.0, erasing=0.0, auto_augment=None)`
    — tắt hết để có tương phản rõ ràng thay vì chỉ tắt 3 tham số nhỏ
    (fliplr/degrees vốn đã yếu, chênh lệch có thể không đủ rõ để kết luận).
  Acceptance: notebook có markdown ghi rõ định nghĩa ON/OFF này (đỡ phải
  đoán lại khi đọc report sau).

- **T3.2 — Train variant OFF**
  Gọi `train()` với các tham số OFF ở T3.1, **giữ nguyên**
  `model="yolov8n.pt"`, `seed=42`, `epochs=50`, `imgsz=640` (y hệt
  baseline) — chỉ augmentation khác. `name="yolov8n_v1_ablation_noaug"`
  (khác baseline `yolov8n_v1_baseline`, không ghi đè — cần cả 2 để so
  sánh). Cả 2 lần gọi `train()` (baseline lẫn variant) đều truyền
  `exist_ok=True` — Ultralytics mặc định `exist_ok=False` và tự tăng hậu
  tố thư mục (`_2`, `_3`, ...) nếu tên đã tồn tại, sẽ làm lệch tên thư mục
  mà T3.3 dùng để đọc `results.csv` nếu 1 trong 2 cell train lỡ chạy lại
  (vd sau khi Colab session ngắt giữa chừng).
  Acceptance: `runs/detect/yolov8n_v1_ablation_noaug/` được tạo, có
  `results.csv`, `weights/best.pt`, nằm trong Drive (giống T2.4).

- **T3.3 — Bảng so sánh baseline vs variant**
  Đọc `results.csv` của **cả 2 run** bằng pandas (không chỉ dùng biến
  `results` trong RAM — session Colab có thể đã restart từ lúc train
  baseline ở Giai đoạn 2, biến đó không còn; đọc từ file trên đĩa đảm bảo
  đúng dù chạy notebook trong session mới): lấy dòng epoch cuối cùng, cột
  `metrics/mAP50(B)`, `metrics/mAP50-95(B)`, và cột `time` (giây, cumulative
  — Ultralytics tự ghi) làm "thời gian train". Lập bảng 2 dòng (ON/OFF) ×
  3 cột (mAP@0.5, mAP@0.5:0.95, thời gian train).
  Acceptance: bảng in ra trong notebook (DataFrame hoặc markdown table),
  đủ 2 dòng đủ 3 cột, số thật từ file trên đĩa.

- **T3.4 — Chọn config thắng, ghi lý do**
  Sau khi có bảng thật: nếu mAP hai bên gần nhau (baseline Giai đoạn 2 đã
  rất cao — 0.9923/0.8435 — nên OFF có thể không kém nhiều, hoặc thậm chí
  cao hơn do dataset nhỏ/đơn giản), ưu tiên **augmentation ON** làm chính
  thức trừ khi OFF vượt trội rõ rệt — lý do: augmentation giúp tổng quát
  hoá tốt hơn cho ảnh/video thật ngoài dataset (mục tiêu triển khai thực
  tế của bài toán), không chỉ tối ưu mAP trên tập test cùng phân bố.
  Quyết định cuối cùng dựa trên số thật, không đoán trước — ghi kết luận +
  lý do vào `docs/problem_statement.md` (mục mới "Ablation" hoặc bổ sung
  mục Dataset/Training hiện có).
  Acceptance: `docs/problem_statement.md` có bảng so sánh + 1 đoạn kết
  luận + lý do chọn, `docs/requirement_checklist.md` mục 3 có thể đánh dấu
  liên quan tới "ablation" (không tick cả mục 3 vì mục 3 còn cần các phần
  khác đã có sẵn — chỉ đảm bảo phần ablation có bằng chứng).

## File/module liên quan

- `notebooks/02_train_detector.ipynb` — **thêm cell** vào cuối (không tạo
  notebook mới — đây vẫn là notebook training, Giai đoạn 3 không có dòng
  "File:" riêng trong PLAN.md, tự nhiên nối tiếp Giai đoạn 2 trong cùng
  file).
- `docs/problem_statement.md` — thêm bảng so sánh + kết luận (T3.4).
- Không sửa `src/models/train.py` — `train()` đã nhận `**kwargs`, đủ để
  gọi với augmentation OFF mà không cần đổi chữ ký.

## Bằng chứng / số liệu kỳ vọng

- `runs/detect/yolov8n_v1_ablation_noaug/results.csv` + `weights/best.pt`
  tồn tại trên Drive.
- Bảng so sánh 2×3 (ON/OFF × mAP@0.5, mAP@0.5:0.95, thời gian train) với
  số thật.
- 1 đoạn kết luận trong `docs/problem_statement.md`: chọn config nào +
  lý do, dựa trên bảng trên.

## Cách bạn tự test sau khi tôi xong

1. Trên Colab, mở lại `02_train_detector.ipynb` (đã pull code mới nếu
   cần), chạy từ đầu tới hết phần Giai đoạn 2 (Setup, git pull, cài deps —
   **không cần train lại baseline**, số liệu baseline đã có sẵn ở
   `results.csv` trên Drive từ lần trước).
2. Chạy tiếp các cell mới (T3.1–T3.4): train variant OFF (~vài chục phút,
   giống baseline), rồi bảng so sánh tự đọc từ 2 file `results.csv`.
3. Xem bảng in ra — kiểm tra số hợp lý (OFF thường mAP thấp hơn hoặc bằng
   ON, trừ khi dataset đủ "dễ" để augmentation không giúp ích).
4. Gửi lại bảng (hoặc chỉ 3 số: mAP@0.5 OFF, mAP@0.5:0.95 OFF, thời gian
   train OFF) cho mình để ghi kết luận vào `docs/problem_statement.md`
   (T3.4) và đóng Giai đoạn 3.

## ❓ Quyết định cần bạn chốt

Không có — định nghĩa ON/OFF, tiêu chí chọn config thắng (ưu tiên ON trừ
khi OFF vượt trội rõ rệt) đã chốt cụ thể ở trên dựa trên mục tiêu tổng
quát hoá của bài toán, không phải chọn thuần theo mAP cao nhất trên test
set.

## Rủi ro / điều cần lưu ý

- Baseline Giai đoạn 2 mAP đã rất cao (0.9923/0.8435) — ablation có thể
  cho kết quả gần như không đổi (dataset "dễ", model đã gần bão hoà). Đây
  vẫn là kết quả hợp lệ để báo cáo (rubric chỉ cần "≥1 ablation" chạy
  đúng, không yêu cầu phải cho thấy cải thiện lớn).
- Không thể chạy training thật trong môi trường CLI này (không GPU) —
  smoke test chỉ ở mức cú pháp/import cho cell mới, xem "Cách bạn tự test"
  để có kết quả thật.
- Nếu Colab session giữa 2 lần train (baseline cũ, variant OFF mới) khác
  nhau về GPU thực tế được cấp (T4 luôn, nhưng load máy chủ Google có thể
  khác), thời gian train so sánh có thể lệch nhẹ do yếu tố ngoài kiểm
  soát — không phải lỗi, chỉ là nhiễu bình thường khi so sánh trên free
  tier.

## Implementation notes

- **Code (T3.1–T3.3 cells + T3.4 placeholder) — done.** Thêm 5 cell vào
  cuối `notebooks/02_train_detector.ipynb`: markdown định nghĩa ON/OFF
  (T3.1), train variant OFF (T3.2, `**kwargs` tắt toàn bộ augmentation),
  bảng so sánh đọc từ `results.csv` trên đĩa bằng pandas (T3.3), markdown
  placeholder chờ điền kết luận (T3.4). Thêm mục "Ablation (Giai đoạn 3)"
  vào `docs/problem_statement.md` với bảng placeholder (baseline đã có số
  thật, OFF chờ chạy).
  - Review: `cv-architecture-review` 2 lần + `code-review` (medium).
    1 finding ở lần đầu: cả 2 lệnh gọi `train()` không có `exist_ok=True`
    → nếu 1 trong 2 cell lỡ chạy lại (vd Colab ngắt giữa chừng), Ultralytics
    tự tăng hậu tố thư mục (`_2`, `_3`, ...), làm lệch với path cố định mà
    cell T3.3 dùng để đọc `results.csv` → sửa: thêm `exist_ok=True` vào cả
    2 lệnh gọi `train()` (baseline lẫn variant). Lần review thứ 2 xác nhận
    sạch, chỉ còn 1 gợi ý nhỏ không phải lỗi (cell T3.3 nên tự import
    `Path` thay vì dựa vào cell trước đó đã chạy) — đã áp dụng luôn cho
    chắc.
  - Smoke test: JSON + cú pháp notebook hợp lệ, `py_compile` qua
    `src/models/train.py`. Đã tự viết `results.csv` giả (đúng format cột
    có khoảng trắng đầu như Ultralytics thật xuất ra) và chạy thử hàm
    `last_epoch_stats()`/bảng so sánh trong `.venv` — logic đọc cột đúng,
    `df.columns.str.strip()` xử lý đúng quirk khoảng trắng. Không chạy
    `train()` thật (cần GPU + dataset thật).
- **T3.1–T3.4 (chạy thật trên Colab + kết luận) — deferred.** Cần bạn tự
  chạy phần ablation mới trong `02_train_detector.ipynb` trên Colab, xem
  "Cách bạn tự test" ở trên, rồi gửi lại số liệu để mình điền T3.4 +
  `docs/problem_statement.md`.
