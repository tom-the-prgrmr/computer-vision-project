# Spec — G1. Data (rubric: mục 2 — Dữ liệu)

**Plan source:** `docs/PLAN.md` — Giai đoạn 1 (`T1.1`–`T1.6`)
**Status:** implemented

## Mục tiêu

Tải dataset v1 (5 lớp, bbox có sẵn từ Roboflow) về, xác nhận cấu trúc đúng,
khám phá phân bố lớp + kiểm tra nhãn bằng mắt, chốt augmentation dùng cho
Giai đoạn 2, và ghi lại toàn bộ số liệu/quyết định vào
`docs/problem_statement.md` để làm bằng chứng cho rubric mục 2 (Dữ liệu).

## Việc cụ thể

- **T1.1 — Tải data**
  Chạy `scripts/download_data.sh` (cần `ROBOFLOW_API_KEY` — đã set ở T0.2)
  hoặc gọi trực tiếp đoạn Roboflow Python API tương đương trong notebook.
  Acceptance: `data/raw/yoga_v1/{train,valid,test}/images` +
  `.../labels` + `data/raw/yoga_v1/data.yaml` tồn tại và không rỗng.
  **Thực hiện bởi:** người dùng, trên Colab (cần mạng + Roboflow key —
  ngoài phạm vi CLI này).

- **T1.2 — Đếm lớp/ảnh mỗi split**
  Load `data.yaml` (`yaml.safe_load`), in `names` (danh sách lớp) và đếm số
  file trong mỗi `images/` split.
  Acceptance: notebook in ra bảng `class × count` tổng và bảng
  `split × count` (train/valid/test).

- **T1.3 — Biểu đồ phân bố lớp**
  Bar chart số ảnh/lớp (dùng tổng train+valid+test, hoặc tách theo split
  nếu muốn chi tiết hơn) bằng matplotlib.
  Acceptance: hình lưu vào notebook output (không cần file riêng), kèm 1-2
  câu nhận xét lớp nào lệch (nếu có).

- **T1.4 — Sanity-check bbox**
  Với 2-3 ảnh mỗi lớp, vẽ bbox từ file `.txt` YOLO-format lên ảnh gốc
  (convert normalized xywh → pixel xyxy) bằng matplotlib/PIL, hiển thị
  trong notebook.
  Acceptance: ít nhất 2 ảnh × 5 lớp = 10 ảnh có bbox vẽ đúng vị trí học
  viên trong notebook output; ghi 1 câu nhận xét nhãn ổn hay có vấn đề.

- **T1.5 — Chốt augmentation**
  Quyết định giá trị cụ thể cho `flipud`, `fliplr`, `degrees` dùng khi train
  YOLOv8 ở Giai đoạn 2. Lý do đã chốt sẵn trong `docs/REQUIREMENTS.md`/
  `CLAUDE.md`: tắt `flipud` (lật dọc làm tư thế yoga vô nghĩa — người lộn
  ngược), giữ `fliplr` (trái/phải đối xứng, an toàn), giới hạn `degrees`
  thấp (xoay mạnh làm sai lệch góc khớp, ảnh hưởng cả bbox lẫn ý nghĩa tư
  thế sau này ở lớp rule-based).
  Acceptance: 1 dòng cấu hình cụ thể ghi trong notebook + spec này, vd
  `flipud=0.0, fliplr=0.5, degrees=10`. Giá trị `fliplr`/`degrees` chính
  xác có thể chỉnh sau khi nhìn ảnh T1.4 (vd nếu ảnh gốc đã đủ đa dạng góc
  chụp thì giảm `degrees` xuống nữa).

- **T1.6 — Ghi kết quả vào `docs/problem_statement.md`**
  Sau khi có số liệu thật từ T1.1-T1.5, thêm/điền mục "Data" gồm: nguồn
  (Roboflow "YOLO YOGA Dataset" v1), số lớp + tên lớp, số ảnh mỗi split,
  nhận xét imbalance, augmentation đã chốt + lý do.
  Acceptance: mục "Data" trong `docs/problem_statement.md` có số liệu thật,
  không còn placeholder/kế hoạch.
  **Thực hiện bởi:** Claude, sau khi người dùng cung cấp số liệu thật từ
  T1.1-T1.5 (không tự bịa số).

## File/module liên quan

- `notebooks/01_data_exploration.ipynb` — **chưa tồn tại**, sẽ tạo khung
  (markdown + code cell) cho T1.1-T1.5 trong bước implement, các cell cần
  chạy thật (tải data, in số liệu, vẽ hình) để trống/TODO vì cần chạy trên
  Colab với data thật.
  - Cell 1 (markdown): tiêu đề + mục tiêu notebook.
  - Cell 2 (code, T1.1): gọi `!bash scripts/download_data.sh` hoặc
    Roboflow Python API trực tiếp (tương đương script, để chạy được cả
    khi không có bash trong Colab).
  - Cell 3 (code, T1.2): load `data.yaml`, in bảng class × count, split ×
    count.
  - Cell 4 (code, T1.3): bar chart phân bố lớp.
  - Cell 5 (code, T1.4): vẽ bbox lên ảnh mẫu.
  - Cell 6 (markdown, T1.5): ghi giá trị augmentation đã chốt + lý do.
- `scripts/download_data.sh` — đã có sẵn, không cần sửa.
- `docs/problem_statement.md` — mục "Data" (T1.6).

## Bằng chứng / số liệu kỳ vọng

- Bảng số ảnh/lớp/split thật (không phải placeholder).
- 1 biểu đồ phân bố lớp (trong notebook output).
- 10 ảnh sanity-check bbox (trong notebook output).
- 1 dòng augmentation config cụ thể + lý do, khớp giữa notebook và
  `docs/problem_statement.md`.

## Cách bạn tự test sau khi tôi xong

1. Mở `notebooks/01_data_exploration.ipynb` trên Colab (đã clone vào Drive
   ở T0.4), đảm bảo `ROBOFLOW_API_KEY` đã có trong Colab Secret (T0.3).
2. Chạy tuần tự các cell — cell tải data cần mạng + vài chục giây tới vài
   phút tuỳ tốc độ Roboflow.
3. Xác nhận: `data/raw/yoga_v1/data.yaml` tồn tại, bảng số ảnh in ra hợp
   lý, biểu đồ phân bố lớp hiện đúng, ảnh bbox vẽ khớp vị trí học viên
   trong ảnh.
4. Copy lại số liệu/nhận xét (class list, count/split, imbalance,
   augmentation đã chốt) gửi lại cho mình để ghi vào
   `docs/problem_statement.md` (T1.6) — mình không tự chạy notebook được
   trong môi trường CLI này nên cần số thật từ bạn.

## ❓ Quyết định cần bạn chốt

Không có quyết định kỹ thuật mơ hồ — augmentation đã có hướng chốt sẵn từ
`CLAUDE.md`/`docs/REQUIREMENTS.md` (chỉ cần xác nhận số `degrees` cụ thể
sau khi nhìn ảnh thật, không phải chọn hướng từ đầu).

## Rủi ro / điều cần lưu ý

- T1.1 cần `ROBOFLOW_API_KEY` — nếu T0.2/T0.3 chưa thật sự xong (key chưa
  set đúng chỗ), script/cell sẽ báo lỗi ngay, đó là dấu hiệu quay lại làm
  nốt Giai đoạn 0.
- T1.6 (ghi vào docs) chỉ làm được sau khi có số liệu thật — Claude sẽ
  không tự bịa số liệu để điền cho đủ.

## Implementation notes

- **Tạo khung notebook — done.** `notebooks/01_data_exploration.ipynb` mới,
  6 code cell + markdown tương ứng T1.1-T1.5: lấy `ROBOFLOW_API_KEY` (Colab
  Secret hoặc env var local) → gọi `scripts/download_data.sh` (không
  duplicate logic Roboflow API) → load `data.yaml`, đếm ảnh/lớp/split →
  bar chart phân bố lớp → vẽ bbox sanity-check (2 ảnh/lớp) → markdown ghi
  augmentation đã chốt (`flipud=0.0, fliplr=0.5, degrees=10`, lý do trong
  chính cell đó).
  - Review: `cv-architecture-review` 2 lần — lần 1 sạch với notebook, phát
    hiện 1 finding từ `code-review` (medium): comment trong
    `app/service.py` còn nhắc `app/main.py` thay vì `app/controller.py`
    (stale sau khi bạn tự tách controller/service trước đó) — đã sửa, lần
    2 xác nhận sạch.
  - Smoke test: JSON hợp lệ (`json.load`), từng code cell `ast.parse`
    không lỗi (trừ cell gọi `!bash ...` — cú pháp Jupyter shell-magic,
    không phải Python thuần, không phải lỗi), `py_compile` qua
    `app/service.py`/`main.py`/`controller.py`/`schemas.py` sau khi sửa.
    Không chạy được thật (cần Colab + `ROBOFLOW_API_KEY` + mạng) — đúng
    như spec đã nói trước.
- **T1.1-T1.5 (chạy thật trên Colab) — done.** 2 lần chạy: lần 1 lỗi
  (`bash: scripts/download_data.sh: No such file or directory` — cwd không
  đứng ở repo root; rồi `ModuleNotFoundError: No module named 'roboflow'`
  — Colab runtime mới mất hết package đã cài ở T0.5). Sửa notebook: thêm
  cell "Setup — mount Drive + cd vào repo" (mount + `os.chdir` vào đúng
  thư mục Drive, assert `scripts/`/`data/` tồn tại) và cell "Cài
  dependencies" (`pip install -r requirements.txt`, idempotent, chạy lại
  không sao) ngay đầu notebook. Chạy lại toàn bộ thành công — kết quả thật
  đã lấy về từ file `.ipynb` đã chạy (cells có output/hình).
- **T1.6 (ghi số liệu thật vào `docs/problem_statement.md`) — done.** Số
  liệu lấy trực tiếp từ output notebook (không phải người dùng gõ tay):
  5 lớp (`bridge`, `downward`, `plank`, `shoulderstand`, `tree`), train
  709 / valid 203 / test 101 (tổng 1013 ảnh), phân bố bbox
  downward=248, tree=216, shoulderstand=206, plank=195, bridge=158
  (imbalance nhẹ, ~1.57×). Ảnh sanity-check (T1.4) được trích trực tiếp từ
  `image/png` output trong `.ipynb` và xem bằng mắt: đa số bbox khớp tốt,
  phát hiện 1 ảnh `shoulderstand` (ảnh minh hoạ) có bbox hẹp hơn tư thế
  thực tế — ghi vào mục "Rủi ro/lưu ý" trong `docs/problem_statement.md`
  thay vì bỏ qua. Augmentation giữ nguyên đề xuất ban đầu
  (`flipud=0.0, fliplr=0.5, degrees=10`) — người dùng xác nhận không cần
  chỉnh sau khi xem ảnh thật.

**Giai đoạn 1 hoàn tất** — tất cả T1.1–T1.6 đã tick trong `docs/PLAN.md`.
