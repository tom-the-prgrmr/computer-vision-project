# Spec — g5. Feedback loop cải tiến (rubric: mục 5 — Feedback loop)

**Plan source:** `docs/PLAN.md` — Giai đoạn 5
**Status:** implemented

## Quyết định hướng (T5.1 — đã chốt)

Hướng mặc định trong PLAN.md ("augmentation/oversampling nhắm đúng cặp lớp
hay nhầm") **không áp dụng được**: Giai đoạn 4 xác nhận confusion matrix
sạch — 0 cặp lớp bị nhầm trên 101 ảnh test (xem
`docs/specs/g4-evaluation-error-analysis.md`). Không có "lỗi ở mục 4" để
nhắm vào.

**Hướng đã chọn (người dùng chốt):** thay vì nhắm vào lỗi trong tập test
cùng phân bố (đã hết lỗi), đi tìm lỗi thật trên ảnh/video **ngoài phân bố
dataset Roboflow** (OOD — ảnh chụp điện thoại thật, góc/nền/ánh sáng khác
tập train) — đây chính là kịch bản triển khai thực tế nêu ở
`docs/problem_statement.md` ("Ai dùng, dùng để làm gì"). Nếu tìm thấy lỗi,
áp dụng tweak augmentation tương ứng và so mAP + OOD-accuracy trước/sau.
Nếu không tìm thấy lỗi rõ rệt, đó vẫn là một kết luận thật (model robust ở
mức OOD nhỏ đã test) — không bắt buộc phải "cải thiện được gì đó" bằng mọi
giá.

Lý do không chọn v2 (mở rộng 15-20 lớp): cần GPU vượt free-tier Colab
(theo `CLAUDE.md`), rủi ro thời gian cao với 7 ngày còn lại trước deadline
15/9 và còn 6 giai đoạn (6-11) phía sau.

**Lưu ý ghi vào problem_statement.md:** đây là một điều chỉnh có chủ đích
so với cách diễn giải "từ lỗi ở mục 4" theo nghĩa đen trong
`docs/requirement_checklist.md` — cần nói rõ lý do (mục 4 không còn lỗi để
sửa) để người chấm hiểu đây là quyết định có cơ sở.

## Mục tiêu

Đo lỗi thật của detector baseline (`yolov8n_v1_baseline`, augmentation ON —
config chính thức từ Giai đoạn 3) trên ảnh ngoài phân bố dataset, áp dụng
1 cải thiện cụ thể nếu có lỗi, retrain, và có số liệu trước/sau thật
(mAP trên test set gốc + accuracy trên tập OOD) — đáp ứng rubric mục 5.

## Việc cụ thể

**T5.2a — Thu thập tập ảnh OOD (bên ngoài môi trường này, bạn tự làm):**
- Tối thiểu **10 ảnh**, cố gắng có ít nhất 1 ảnh cho mỗi lớp trong 5 lớp
  (`bridge`, `downward`, `plank`, `shoulderstand`, `tree`) — không bắt buộc
  đều tuyệt đối, ảnh thật khó kiếm hơn ở vài tư thế thì lấy ít hơn cũng
  được, hoặc chỉ phủ 3-4/5 lớp cũng được, miễn tổng ≥ 10.
- Nguồn: chụp bằng điện thoại thật, hoặc **dataset khác trên Kaggle/nơi
  khác** (classification, không cần bbox — chỉ cần ảnh + nhãn lớp), miễn
  là ảnh người thật (tránh ảnh minh hoạ/đồ hoạ — đã có 1 case nhiễu nhãn
  kiểu này ở T1.4).
  - **Điều kiện bắt buộc: phải khác nguồn** Roboflow "YOLO YOGA Dataset"
    mình đang dùng (1013 ảnh, đúng 5 lớp Bridge/Downward Dog/Plank/
    Shoulderstand/Tree) — dataset này cũng bị re-upload dưới tên khác ở
    vài nơi (kể cả Kaggle), nếu vô tình chọn đúng bản mirror thì không còn
    là OOD nữa (cùng ảnh, cùng phân bố, không tìm ra lỗi thật gì). Trước
    khi dùng, kiểm tra nhanh: nếu tổng số ảnh ≈ 1013 và khớp y hệt 5 tên
    lớp trên → bỏ qua, tìm nguồn khác.
  - Không cần đúng tên lớp giống hệt — dataset khác có thể đặt tên khác
    (vd `downdog` thay vì `downward`) — chỉ cần map tên lớp thủ công trong
    code (xem T5.2b), không cần đủ cả 5 lớp.
- Đặt vào thư mục mới `data/ood_samples/`, theo 1 trong 2 cách:
  - Ảnh rời + tên file bắt đầu bằng tên lớp: `tree_01.jpg`, `plank_02.jpg`
  - Hoặc giữ nguyên cấu trúc thư mục con theo lớp nếu tải dataset dạng đó:
    `data/ood_samples/<ten_lop_goc>/*.jpg` (code ở T5.2b đọc cả 2 kiểu)

**T5.2b — Đo baseline OOD accuracy (code, notebook mới):**
- `notebooks/05_feedback_loop_ood.ipynb`: Setup chuẩn (mount Drive → cd
  repo, git pull, pip install) giống các notebook khác.
- Load `runs/detect/yolov8n_v1_baseline/weights/best.pt`, chạy
  `yolo.predict()` trên từng ảnh trong `data/ood_samples/` (dùng lại
  pattern `predict_top_class` kiểu `notebooks/03_evaluation_error_analysis.ipynb`),
  suy nhãn thật từ phần tên file trước dấu `_` **hoặc** tên thư mục cha
  (nếu ảnh nằm trong `data/ood_samples/<ten_lop_goc>/`), qua một dict
  `CLASS_NAME_MAP` khai trong notebook để map tên lớp gốc của dataset khác
  (vd `downdog`) sang đúng tên lớp model (`downward`) — ảnh có tên/thư mục
  không map được thì bỏ qua, in cảnh báo, không crash.
- In bảng: ảnh | nhãn thật | dự đoán | confidence | đúng/sai.
- Vẽ lưới ảnh có box đè lên (`result.plot()`) để soi bằng mắt.
- Tổng kết **OOD accuracy "trước"** = số ảnh đúng / tổng số ảnh.

**T5.3 — Áp tweak augmentation dựa trên loại lỗi quan sát được (code):**

Bảng mapping cố định (chọn sẵn để không phải đoán giữa chừng khi thấy lỗi
thật):

| Lỗi quan sát trên ảnh OOD | Tweak augmentation trong `train()` |
|---|---|
| Miss/sai vì ảnh tối/sáng hơn tập train | tăng `hsv_v` (range độ sáng) |
| Miss vì người nhỏ/xa camera hơn tập train | tăng `scale` (range zoom out) |
| Sai lớp vì nền lộn xộn/nhiều người khác trong khung | tăng `mosaic`, cân nhắc bật `copy_paste` |
| Miss vì ảnh mờ/góc nghiêng khác thường | tăng nhẹ `degrees`/`shear` |
| Không có lỗi rõ rệt (OOD accuracy đã cao, ví dụ ≥ 90%) | **Không retrain** — kết luận "baseline đã robust trên OOD nhỏ đã test", đóng giai đoạn với số liệu thật này |

- Nếu có ≥1 lỗi rõ rệt: chọn đúng 1 dòng khớp nhất với lỗi thấy nhiều nhất,
  chỉ đổi tham số đó (giữ nguyên các augmentation khác so với baseline ON),
  retrain qua `src/models/train.py::train()` đã có sẵn — cùng
  `model="yolov8n.pt"`, `seed=42`, `epochs=50`, `imgsz=640`, tên run mới
  **`yolov8n_v1_feedback_v2`** (không ghi đè `yolov8n_v1_baseline`, cần cả
  2 để so sánh — giống cách Giai đoạn 3 đã làm).

**T5.4 — Bảng so sánh trước/sau (code, cùng notebook):**
- Chạy lại đúng tập OOD (hàm ở T5.2b) với checkpoint mới → OOD accuracy
  "sau".
- Chạy `model.val()` trên test set gốc (`data/raw/yoga_v1/data.yaml`) với
  checkpoint mới → mAP@0.5, mAP@0.5:0.95 "sau" — so với baseline ON
  (0.9922 / 0.8352) để xác nhận **không thoái hoá** trên phân bố gốc.
- Bảng: OOD accuracy trước/sau, mAP@0.5 trước/sau, mAP@0.5:0.95 trước/sau,
  thời gian train.

**T5.5 — Ghi kết luận (docs):**
- `docs/problem_statement.md`: mục mới "Feedback loop cải tiến (Giai đoạn
  5)" — nêu lý do đổi hướng (xem trên), số liệu trước/sau, kết luận.
- Đánh dấu mục 5 `[x]` trong `docs/requirement_checklist.md`.

## File/module liên quan

- `data/ood_samples/` — ảnh mới, **do bạn thêm** (ngoài môi trường này)
- `notebooks/05_feedback_loop_ood.ipynb` — mới
- `src/models/train.py` — dùng lại `train()` hiện có, không sửa chữ ký trừ
  khi thiếu tham số augmentation cần dùng
- `docs/problem_statement.md`, `docs/requirement_checklist.md`,
  `docs/PLAN.md`

## Bằng chứng / số liệu kỳ vọng

- Bảng: OOD accuracy trước/sau, mAP@0.5 + mAP@0.5:0.95 trước/sau (test set
  gốc), thời gian train
- Lưới ảnh OOD có box vẽ đè, nhãn đúng/sai rõ ràng
- Nếu không retrain (baseline đã robust): số liệu OOD accuracy "trước" đủ
  cao (≥90%) làm bằng chứng, không cần bảng trước/sau

## Cách bạn tự test sau khi tôi xong

1. Chụp/tải ≥10 ảnh OOD theo hướng dẫn T5.2a, đặt vào `data/ood_samples/`,
   commit hoặc đẩy trực tiếp lên Drive (tuỳ bạn — code chỉ cần thư mục này
   tồn tại khi chạy notebook).
2. Trên Colab: mở `notebooks/05_feedback_loop_ood.ipynb`, chạy Setup → git
   pull → cell T5.2b, xem bảng + OOD accuracy "trước".
3. Báo lại cho tôi: OOD accuracy, và loại lỗi quan sát được nếu có (ảnh
   nào sai, vì sao theo bạn) — tôi sẽ áp đúng dòng tương ứng trong bảng
   mapping T5.3 và viết cell retrain.
4. Chạy cell retrain trên Colab (T5.3), rồi cell so sánh trước/sau (T5.4),
   báo lại số liệu để tôi ghi vào docs (T5.5).

## ❓ Quyết định cần bạn chốt

(Không còn — hướng chính đã chốt ở trên qua câu hỏi trước đó.)

## Rủi ro / điều cần lưu ý

- Tập OOD ~10 ảnh nhỏ, không phải benchmark thống kê chắc chắn — chỉ đủ
  minh hoạ pattern lỗi định tính, sẽ ghi rõ giới hạn này trong kết luận,
  không phóng đại thành metric chính thức.
- Việc chọn tweak augmentation ở T5.3 phụ thuộc lỗi thật quan sát được —
  chỉ biết chính xác sau khi có kết quả T5.2b từ bạn; tên tham số
  Ultralytics cụ thể (`hsv_v`, `scale`, `mosaic`, `copy_paste`, `degrees`,
  `shear`) sẽ được xác nhận lại đúng chữ ký khi implement.
- Nếu bạn không kiếm đủ 10 ảnh OOD thật, có thể làm với ít hơn — chỉ cần
  nêu rõ số lượng thật trong kết luận, không fabricate số liệu.

## Implementation notes

**Files touched:** `notebooks/05_feedback_loop_ood.ipynb` (mới, 20 cells).

**T5.2b (đo OOD accuracy):** `collect_ood_samples()` đọc cả 2 kiểu tổ chức
thư mục (file rời tên `<lop>_...`, hoặc thư mục con `<ten_lop_goc>/`), map
qua `CLASS_NAME_MAP`, bỏ qua + cảnh báo ảnh không suy ra được nhãn hợp lệ.
`evaluate_ood()` chạy `yolo.predict()` đúng 1 lần/ảnh, giữ lại `Results`
object để cell vẽ lưới bên dưới dùng lại (tránh predict trùng lặp — xem
review note bên dưới).

**T5.3 (tweak augmentation):** bảng `AUGMENTATION_TWEAKS` cố định 4 loại
lỗi → tham số tương ứng (`hsv_v`, `scale`, `mosaic`+`copy_paste`,
`degrees`+`shear`), biến `OBSERVED_ISSUE` để trống (`None`) — bạn set giá
trị sau khi xem kết quả T5.2b thật, cell retrain tự rẽ nhánh (bỏ qua nếu
`None`, gọi `train()` với đúng 1 tweak nếu có).

**T5.4 (so sánh trước/sau):** dùng lại `BASELINE_MAP50`/`BASELINE_MAP50_95`
đã có thật từ Giai đoạn 3 (0.9922/0.8352) thay vì validate lại baseline —
chỉ validate lại checkpoint mới.

**Review:** `cv-architecture-review` (2 lượt) — sạch cả 2 lượt, không lẫn
lộn 2 lớp kiến trúc, không lẫn rubric mục 5/6, dùng lại đúng
`src/models/train.py::train()`. `code-review` (medium) tìm ra 1 vấn đề
hiệu năng: cell vẽ lưới ảnh gọi `yolo.predict()` lần 2 trên cùng ảnh đã
predict ở `evaluate_ood()` — đã sửa bằng cách giữ lại `Results` object
trong `evaluate_ood()` thay vì predict lại.

**Smoke test:** (1) mọi code cell parse được as valid Python (bỏ qua dòng
`!pip`/`!git`); (2) test logic thật cho `infer_true_class()`/
`collect_ood_samples()` với cấu trúc thư mục giả (folder-mapping,
filename-prefix-mapping, bỏ qua ảnh không map được, bỏ qua file không phải
ảnh) — cả 2 đều pass. Phần cần GPU/model thật (predict, train, val) không
smoke-test được ở đây — cần chạy thật trên Colab.

**T5.2a — đã xong:** 18 ảnh OOD (6/lớp × downdog/plank/tree) từ Kaggle
`niharika41298/yoga-poses-dataset`, xem `data/ood_samples/README.md`.

**Bug thật gặp khi chạy T5.2b trên Colab (đã sửa):** `result.names` trả
tên lớp gốc của model kèm tiền tố `"yoga-pose "` (vd `"yoga-pose
downward"` — data.yaml v1 vốn có tiền tố này, xem
`docs/problem_statement.md`), nhưng `top_class_from_result()` không bỏ
tiền tố trước khi so với `MODEL_CLASSES`/nhãn thật → **mọi dự đoán đều bị
tính SAI dù model đoán đúng nội dung** (log Colab đầu tiên báo 0/18 =
0.0%). Sửa bằng `raw_name.removeprefix("yoga-pose ").strip()`. Verify:
đối chiếu tay log gốc (18 dòng, cột "đoán" đều đúng khớp cột "thật" trừ 1
dòng) + smoke test logic prefix-stripping.

**T5.2b — kết quả thật (sau khi sửa bug, từ log Colab gốc — không cần
chạy lại vì log đã đủ dữ liệu để tính đúng):**

OOD accuracy = **17/18 = 94.4%**. Đúng 1 lỗi thật:
`plank/00000089.jpg` — thật = `plank`, model đoán `tree` (conf 0.82).
Nhìn ảnh: tư thế đứng dựa tường, tay giơ cao — không giống plank kinh
điển, khả năng cao là nhãn gốc trong dataset Kaggle không chuẩn (rủi ro
nhiễu nhãn dataset ngoài, không phải lỗi hệ thống của model) hơn là một
pattern lỗi thật cần sửa.

**T5.3 — quyết định:** 94.4% ≥ ngưỡng 90% đã chốt sẵn trong spec, và lỗi
duy nhất không khớp rõ dòng nào trong bảng `AUGMENTATION_TWEAKS` (không
tối, không nhỏ/xa, không mờ, nền không đặc biệt lộn xộn) — giữ
`OBSERVED_ISSUE = None`. **Không retrain.** Kết luận: baseline
(`yolov8n_v1_baseline`) đã robust trên tập OOD 18 ảnh đã test.

**Deferred:** T5.4 (bảng trước/sau) không áp dụng vì không retrain — đã
có đủ bằng chứng ở T5.2b. T5.5 (ghi kết luận vào
`problem_statement.md`/`requirement_checklist.md`) làm ở bước đóng giai
đoạn tiếp theo.
