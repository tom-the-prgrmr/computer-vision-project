# Spec — g12. Sửa rò rỉ dữ liệu & đo hiệu năng trên PROD (rubric: mục 4 — Evaluation, mục 5 — Feedback loop, mục 7 — Deployment)

**Plan source:** `docs/PLAN.md` — Giai đoạn 12
**Status:** draft <!-- draft -> implemented (set at close-out) -->

## Bối cảnh — 3 vấn đề phát hiện sau khi đã "xong" Giai đoạn 1-11

1. **Tập test/valid chứa ảnh augmented của chính tập train.** README của
   Roboflow ghi "No image augmentation", nhưng kiểm tra thật cho thấy nhiều
   ảnh test/valid là **ảnh train lật ngang** (cùng tên gốc `0000xxxx_jpg`,
   cùng lớp). Đã xem tận mắt 8 cặp ngẫu nhiên, cả 8 đều là ảnh gương. Số
   đã chốt sau khi hiệu chỉnh cách phát hiện trùng (xem Implementation
   notes — tên gốc + lớp, dHash 16×16 có tính bản lật, ORB + RANSAC cho bản
   bị crop/zoom):

   | Split | Tổng | Rò rỉ từ train | Sạch |
   |---|---|---|---|
   | valid | 203 | 122 | 81 |
   | test | 101 | 59 | 42 |

   Train có bật `fliplr=0.5`, nên model đã thấy gần như y hệt các ảnh test
   này lúc học. Valid cũng rò rỉ, nên việc chọn `best.pt` / early stopping
   cũng bị lệch.

2. **Performance đang đo trên môi trường training, không phải PROD.** Bảng
   206ms (ONNX) / 248ms (PyTorch) ở Giai đoạn 7 đo trên **GPU T4 Colab**.
   PROD (Render, CPU free tier) mới có vài lần đo tay (~4.7–8.4s/ảnh),
   chưa có stress test: chưa có p50/p95/p99, throughput, error rate theo
   số request đồng thời, hay cold start. Thêm nữa, route `predict` trong
   `app/controller.py` là `async def` nhưng gọi
   `service.predict_image()` đồng bộ (ONNX + MediaPipe), nên các request
   đồng thời bị xếp hàng nối tiếp trên event loop.

3. **Chỉ số quá cao nên "không có gì để improve".** Đây là hệ quả của vấn
   đề 1. Đo nhanh `models/best.onnx` hiện tại (CPU local, recall theo đúng
   lớp ở IoU ≥ 0.5, conf ≥ 0.25):

   | Tập | Số ảnh | Recall | FP |
   |---|---|---|---|
   | test rò rỉ | 59 | 0.984 | 0 |
   | test sạch | 42 | **0.905** | 5 |
   | valid rò rỉ | 122 | 0.992 | 5 |
   | valid sạch | 81 | 0.963 | 4 |

   Tỉ lệ lỗi tăng khoảng 6 lần trên phần sạch. 42 ảnh còn là mẫu nhỏ,
   nhưng chiều hướng thì rõ. Kết luận ở Giai đoạn 4 ("0 cặp lớp bị nhầm")
   và Giai đoạn 5 ("không cần retrain") dựa trên số liệu không đáng tin.

## Mục tiêu

- Có một split **không rò rỉ** và số liệu mAP **trung thực** cho detector.
- Có **lỗi thật** để phân tích, và làm lại mục 5 (Feedback loop) với một vòng
  cải tiến có bảng trước/sau thật.
- Có số liệu performance **đo trên PROD đã deploy** (Render), kèm một vòng
  cải tiến deployment có số trước/sau.
- Sửa lại tài liệu (problem_statement, README, slide) cho khớp số liệu mới,
  nói thẳng số cũ bị thổi phồng vì rò rỉ. Không giấu.

## Việc cụ thể

**T12.1 — Công cụ phát hiện rò rỉ (code, local):**
- `src/data/dedup_split.py`, hàm `find_duplicate_groups(dataset_dir)`: gom
  ảnh của cả 3 split thành nhóm. Hai ảnh cùng nhóm nếu (a) cùng tên gốc
  (phần trước `_jpg.rf.`) **và** cùng lớp, hoặc (b) dHash 8×8 của ảnh, hoặc
  của bản lật ngang, cách nhau ≤ 10 bit. Dùng union-find để nhóm bắc cầu.
- Hàm `leakage_report(groups)`: số ảnh valid/test có nhóm chung với train.
- **Nghiệm thu:** chạy trên `data/raw/yoga_v1` ra đúng con số ở bảng bối
  cảnh (test 59/101, valid 122/203), hoặc lệch nhỏ và giải thích được nếu
  union-find gom thêm nhóm bắc cầu.

**T12.2 — Chia lại split theo nhóm (code, local):**
- Hàm `group_split(groups, ratios=(0.70, 0.15, 0.15), seed=42)`: mỗi nhóm
  nằm trọn trong **1** split. Phân tầng theo lớp (stratify theo lớp của
  nhóm) để mỗi split giữ tỉ lệ lớp gần với tổng thể.
- Ghi ra `data/processed/yoga_v1_clean/{train,valid,test}/{images,labels}`
  + `data.yaml` (giữ nguyên `names` gốc có tiền tố `yoga-pose ` để
  `CLASS_NAMES` của app không đổi).
- Ghi manifest `data/splits/yoga_v1_clean_manifest.csv` (file, nhóm, lớp,
  split cũ, split mới), **commit vào git**. Colab dựng lại
  `data/processed/yoga_v1_clean/` từ manifest này.
- Tỉ lệ 70/15/15 thay vì 70/20/10 của bản gốc: test gốc chỉ có 101 ảnh, và
  sau khi bỏ trùng còn ít nhóm độc lập, nên tăng test lên để mAP bớt nhiễu.
- **Nghiệm thu:** chạy lại `leakage_report` trên split mới → **0** nhóm cắt
  ngang split. In số ảnh và số nhóm mỗi split, phân bố lớp mỗi split.

**T12.3 — Đo lại model cũ một cách trung thực (code + Colab):**
- **Không** dùng test của split mới để đo model cũ: split mới có thể chứa
  ảnh mà model cũ đã train. Thay vào đó, đo model cũ trên **42 ảnh test
  sạch của split gốc** (sạch so với train gốc, chính là tập model cũ đã
  học).
- Cell mới trong `notebooks/03_evaluation_error_analysis.ipynb`: tạo
  `data.yaml` tạm trỏ vào 42 ảnh sạch, chạy `model.val()` với
  `yolov8n_v1_baseline/weights/best.pt` → mAP@0.5, mAP@0.5:0.95,
  confusion matrix. Đặt cạnh số cũ (0.9922 / 0.8352 trên 101 ảnh).
- **Nghiệm thu:** bảng "test gốc 101 ảnh vs test sạch 42 ảnh" với mAP thật
  từ Colab.

**T12.4 — Mở rộng tập OOD (bạn tự làm, ngoài môi trường này):**
- Hiện có 18 ảnh, 3/5 lớp (`data/ood_samples/`). Bổ sung để có **≥ 8
  ảnh/lớp cho đủ 5 lớp** (thêm `bridge`, `shoulderstand`), trong đó cố
  gắng có ảnh **tự chụp bằng điện thoại**, vì đó là đúng loại ảnh người
  dùng gửi lên PROD.
- Giữ cách tổ chức thư mục con theo lớp như cũ, cập nhật
  `data/ood_samples/README.md` (nguồn, số lượng).

**T12.5 — Retrain baseline trên split sạch (Colab):**
- `notebooks/02_train_detector.ipynb`, cell mới: gọi lại
  `src/models/train.py::train()` với cùng config chính thức (`yolov8n.pt`,
  `seed=42`, `epochs=50`, `imgsz=640`, augmentation ON như Giai đoạn 1),
  `data=data/processed/yoga_v1_clean/data.yaml`, tên run
  **`yolov8n_v1_clean_baseline`**. Không ghi đè `yolov8n_v1_baseline`.
- **Nghiệm thu:** mAP@0.5, mAP@0.5:0.95 trên test **mới** (`split="test"`,
  không phải valid).

**T12.6 — Error analysis trên lỗi thật (Colab):**
- Confusion matrix + danh sách ảnh sai (FN, FP, nhầm lớp) của
  `yolov8n_v1_clean_baseline` trên test mới, và OOD accuracy trên tập OOD
  mở rộng (dùng lại `evaluate_ood()` ở `notebooks/05_feedback_loop_ood.ipynb`).
- EigenCAM trên **ảnh sai** (Giai đoạn 4 mới chỉ chạy trên ảnh đúng).
- Gom lỗi thành pattern (người nhỏ/xa, nền rối, tư thế lộn ngược, góc
  chụp lạ, ảnh đồ hoạ...).

**T12.7 — Một vòng cải tiến detector (Colab) — làm lại rubric mục 5:**
- Từ pattern lỗi nhiều nhất ở T12.6, chọn **1** thay đổi (dùng lại bảng
  `AUGMENTATION_TWEAKS` ở Giai đoạn 5; nếu không khớp dòng nào thì cân
  nhắc `yolov8s.pt`). Chỉ đổi đúng 1 biến so với `yolov8n_v1_clean_baseline`.
- Retrain thành run **`yolov8n_v1_clean_feedback`**.
- **Nghiệm thu:** bảng trước/sau: mAP@0.5, mAP@0.5:0.95 (test mới), OOD
  accuracy, số lỗi theo pattern đã nhắm. Nếu không cải thiện thì vẫn ghi
  đúng như vậy, không chọn lại cho đẹp.

**T12.8 — Re-export và redeploy model thắng (code + bạn deploy):**
- Export run thắng (T12.5 hoặc T12.7) ra ONNX qua `src/models/export.py`,
  thay `models/best.onnx` (Git LFS), push để Render build lại.
- **Nghiệm thu:** `/predict` trên PROD trả kết quả bằng model mới (kiểm tra
  bằng một ảnh test mới có kết quả khác model cũ, hoặc so hash file).

**T12.9 — Stress test trên PROD (code, chạy từ máy local vào Render):**
- `scripts/load_test.py`, **chỉ dùng thư viện chuẩn** (`urllib` +
  `concurrent.futures`, không thêm dependency): gửi `POST /predict`
  multipart với 1 ảnh cố định (kích thước như ảnh điện thoại thật, ~1080px
  cạnh dài) tới URL truyền qua `--url`.
- Các phép đo:
  - **Cold start:** sau khi service ngủ (Render free sleep sau ~15 phút
    không có request), thời gian từ request đầu đến khi `/health` trả 200,
    và latency của `/predict` đầu tiên.
  - **Warm, theo mức đồng thời 1 / 2 / 4 / 8:** mỗi mức chạy N = 20
    request. Ghi p50 / p95 / p99 latency phía client, throughput (req/s),
    tỉ lệ lỗi (HTTP ≠ 200 hoặc timeout 60s), và `latency_ms` phía server
    (lấy từ response) để tách thời gian xử lý khỏi thời gian mạng/xếp hàng.
- Xuất CSV thô + bảng tóm tắt vào `docs/perf/prod_load_test_<ngày>.md`.
- Giữ bảng Colab T4 ở Giai đoạn 7 nhưng đổi nhãn rõ thành "benchmark
  offline (GPU training env), không phải PROD".

**T12.10 — Sửa nút thắt và đo lại trên PROD (code + bạn deploy):**
- Đổi route `predict` sang `def` thường (FastAPI tự chạy trong threadpool)
  hoặc giữ `async def` và bọc `await run_in_threadpool(service.predict_image, ...)`.
  Kiểm tra `onnxruntime.InferenceSession.run` và MediaPipe gọi từ nhiều
  thread có an toàn không. MediaPipe `Pose` **không** thread-safe, nên cần
  lock quanh phần MediaPipe hoặc mỗi thread một instance.
- Cân nhắc giới hạn `intra_op_num_threads` của ONNX Runtime theo số CPU
  thật của Render, để nhiều request không tranh nhau CPU.
- Deploy, chạy lại T12.9 với **đúng** cấu hình đo cũ.
- **Nghiệm thu:** bảng trước/sau (p50/p95, throughput, error rate ở mỗi mức
  đồng thời). Nếu CPU Render quá yếu để thấy khác biệt thì ghi đúng như vậy.

**T12.11 — Cập nhật tài liệu:**
- `docs/problem_statement.md`: thêm mục "Phát hiện rò rỉ dữ liệu (Giai
  đoạn 12)" với bảng rò rỉ + số cũ vs số mới. Sửa kết luận ở Giai đoạn 4
  và 5 (giữ lại đoạn cũ, đánh dấu rõ là đã bị thay thế, không xoá lịch
  sử). Thay mục performance bằng số PROD.
- `README.md`, `docs/slides/*`, `docs/requirement_checklist.md` (mục 4, 5,
  7) theo số liệu mới.
- Một slide "Bài học": tin README của dataset mà không kiểm tra, dẫn đến
  số liệu ảo.

## File/module liên quan

- `src/data/dedup_split.py` — mới (T12.1, T12.2)
- `data/splits/yoga_v1_clean_manifest.csv` — mới, commit (T12.2)
- `data/processed/yoga_v1_clean/` — sinh ra từ manifest, không commit
- `notebooks/02_train_detector.ipynb`, `03_evaluation_error_analysis.ipynb`,
  `05_feedback_loop_ood.ipynb` — thêm cell
- `src/models/train.py`, `src/models/export.py` — dùng lại, không đổi chữ ký
  trừ khi thiếu tham số
- `data/ood_samples/` — bạn bổ sung ảnh
- `scripts/load_test.py` — mới (T12.9)
- `app/controller.py`, `app/service.py` — T12.10
- `models/best.onnx` — thay ở T12.8
- `docs/perf/` — mới
- `docs/problem_statement.md`, `README.md`, `docs/slides/*`,
  `docs/requirement_checklist.md`, `docs/PLAN.md`

## Bằng chứng / số liệu kỳ vọng

- Bảng rò rỉ split gốc, và xác nhận 0 rò rỉ trên split mới.
- mAP model cũ: 101 ảnh test gốc vs 42 ảnh test sạch.
- mAP + confusion matrix + OOD accuracy của `yolov8n_v1_clean_baseline`.
- Bảng trước/sau của `yolov8n_v1_clean_feedback` (rubric mục 5).
- Bảng stress test PROD trước/sau sửa route (rubric mục 7).

## Cách bạn tự test sau khi tôi xong

1. Local: `python -m src.data.dedup_split data/raw/yoga_v1` → xem báo cáo
   rò rỉ, thư mục `data/processed/yoga_v1_clean/` và dòng "0 nhóm cắt
   ngang split".
2. Colab: chạy cell T12.3 (model cũ trên 42 ảnh sạch), T12.5 (retrain),
   T12.6, T12.7. Báo lại số liệu cho tôi ghi vào docs.
3. PROD: `python scripts/load_test.py --url https://computer-vision-project-hl82.onrender.com`
   trước khi sửa route, rồi chạy lại sau khi Render deploy bản đã sửa.
   Mở trang web thật trên điện thoại để chắc demo vẫn chạy.

## ❓ Quyết định cần bạn chốt

(Không còn. Đã chốt:)
1. **Stress test lên Render PROD: đồng ý** (tối đa 8 request đồng thời).
2. **Chia lại toàn bộ dữ liệu** (T12.2) và train lại (T12.5).
3. **Quota Colab: đủ** cho các lần retrain T12.5/T12.7.

**Quyết định kỹ thuật khi implement:** `data/processed/` bị `.gitignore`,
Colab lấy data bằng cách tải lại từ Roboflow. Để split giống hệt giữa máy
local và Colab, `dedup_split.py` ghi split vào manifest **được commit**
`data/splits/yoga_v1_clean_manifest.csv`. Colab chỉ **áp** manifest này
(copy file theo cột split mới), không tính lại dHash, vì dHash có thể lệch
nhẹ giữa các phiên bản Pillow.

## Rủi ro / điều cần lưu ý

- Sau khi bỏ trùng, số nhóm ảnh độc lập ít hơn nhiều so với 1013 (ước
  lượng vài trăm nhóm), nên test 15% vẫn chỉ khoảng 100 ảnh độc lập.
  mAP vẫn còn nhiễu, cần ghi rõ giới hạn này.
- Gom theo tên gốc (`00000006`) có thể gộp nhầm 2 ảnh khác nhau trùng số.
  Việc này chỉ làm nhóm to hơn (an toàn hơn về rò rỉ), không gây rò rỉ.
  dHash ngưỡng 10 có thể bỏ sót bản augment mạnh (crop/xoay lớn); spot-check
  bằng mắt một lưới cặp ảnh sau khi chia.
- Số liệu stress test trên Render free phụ thuộc tải chung của nền tảng,
  nên chạy mỗi cấu hình ít nhất 2 lần và ghi giờ chạy.
- Đổi model ở PROD (T12.8) có thể làm `POSE_RULES` (Giai đoạn 6) cho kết
  quả khác do box crop khác. Chạy lại `scripts/manual_test_score_pose.py`
  sau khi đổi model.
- Rubric mục 6 (form scoring) **không** thuộc giai đoạn này. Vẫn giữ tách
  biệt theo `CLAUDE.md`.

## Implementation notes

**Files touched:** `src/data/dedup_split.py` (mới), `data/splits/yoga_v1_clean_manifest.csv`
(mới, commit), `src/evaluation/metrics.py` (`load_confusion_matrix(split=...)`,
`per_image_errors()` mới), `notebooks/06_clean_split_retrain.ipynb` (mới, 27 cell —
gom T12.2/T12.3/T12.5–T12.7 vào 1 notebook thay vì chèn vào 02/03/05, để các notebook
cũ giữ nguyên làm bằng chứng lịch sử Giai đoạn 2-5), `scripts/load_test.py` (mới),
`app/controller.py`, `app/service.py` (T12.10), `docs/perf/` (mới).

**T12.1 — tiêu chí trùng lặp đã đổi so với spec (hiệu chỉnh trên dữ liệu thật):**
- dHash 8×8 ngưỡng 10 (như spec viết) **gộp nhầm**: tỉ lệ khớp nhầm mỗi cặp chỉ 0.15%,
  nhưng trên ~513k cặp union-find nối bắc cầu thành 1 nhóm 106 ảnh gồm nhiều người
  khác nhau cùng tư thế `tree` trên nền trắng (đã xem tận mắt). Chuyển sang dHash
  16×16 ngưỡng 12: 371/371 cặp trùng đã biết cách nhau 0–1 bit, cặp ngẫu nhiên ≥ 26.
- dHash **bỏ sót** bản sao bị zoom/crop (xem tận mắt: tree, downward, shoulderstand).
  Không chỉnh ngưỡng được vì chồng lấn với cặp khác người (19–25 bit). Thêm bước xác
  minh hình học: với 10 láng giềng gần nhất theo dHash toàn ảnh **và** theo dHash
  vùng bbox (crop theo bbox triệt tiêu khác biệt zoom), so khớp ORB + RANSAC (có tính
  bản lật). Cặp trùng đã biết ≥ ~430 inlier, cặp không liên quan đa số < 10; chọn
  ngưỡng 25 (số rò rỉ ổn định ở mọi ngưỡng 20–40, nhóm lớn nhất 11 ảnh).
- Kiểm tra độc lập sau khi chia: ORB so **toàn bộ** cặp test/valid × train cùng lớp —
  còn sót đúng 1 bản sao thật (cùng 1 hình minh hoạ `bridge`, khác nền); các cặp
  điểm cao tiếp theo (≤ 46 inlier) là khớp nhầm do chữ/watermark. Chấp nhận, ghi là
  giới hạn.

**Số liệu rò rỉ chốt (đã cập nhật vào bảng ở mục Bối cảnh):**

| Split gốc | Tổng | Rò rỉ từ train | Sạch |
|---|---|---|---|
| valid | 203 | 122 | 81 |
| test | 101 | 59 | 42 |

1013 ảnh → **552 nhóm độc lập**. Split mới (70/15/15, phân tầng theo lớp, seed 42):
train 703 ảnh/383 nhóm, valid 156/81, test 154/88 — **0 nhóm cắt ngang split**.

**T12.3 — xong ở local (không cần Colab):** Ultralytics `val()` chạy thẳng trên
`models/best.onnx` (đúng model đang chạy PROD), CPU:

| Test gốc | mAP@0.5 | mAP@0.5:0.95 | P | R |
|---|---|---|---|---|
| đủ 101 ảnh (có rò rỉ) | 0.994 | 0.767 | 0.992 | 0.981 |
| 42 ảnh sạch | 0.991 | 0.716 | 0.979 | 0.957 |

Kết luận trung thực: rò rỉ thổi phồng **mAP@0.5:0.95 ~5pp** và recall ~2.4pp, nhưng
**mAP@0.5 gần như không đổi** — v1 vẫn thật sự dễ ở IoU 0.5. Lỗi thật nằm ở độ khít
box (thấp nhất `tree` 0.64, `shoulderstand` 0.68) và ở ảnh ngoài phân bố → T12.4 (mở
rộng OOD) quan trọng hơn dự kiến ban đầu. (0.767 ONNX/CPU lệch so với 0.8352 `.pt`/GPU
ở Giai đoạn 3 do khác backend/letterbox; notebook 06 đo lại bằng `.pt` để cùng điều kiện.)

**T12.9 — PROD "before" (Render free, 2026-10-27 15:43 UTC),** `docs/perf/prod_load_test_20261027_1537_before.md`:

| Đồng thời | OK/N | p50 client | p95 client | Server p50 | Throughput |
|---|---|---|---|---|---|
| 1 | 20/20 | 5.2s | 6.3s | 4.9s | 0.19 req/s |
| 2 | 20/20 | 9.7s | 10.9s | 4.8s | 0.20 req/s |
| 4 | 18/20 | 11.1s | 42.1s | 4.7s | 0.21 req/s |
| 8 | 15/20 | 21.7s | 49.1s | 4.9s | 0.18 req/s |

Server luôn ~4.8s/ảnh, client tăng tuyến tính theo số đồng thời → xếp hàng nối tiếp;
ở 4–8 đồng thời có HTTP 502 + timeout (tới 25% lỗi). Cold start chưa đo bằng script
(lần ping `/health` đầu tiên treo > 120s khi service đang ngủ — chưa đủ chính xác để
ghi số).

**T12.10 — đã deploy, đo "after" trên PROD (2026-10-28 17:57 UTC),**
`docs/perf/prod_load_test_20261028_1753_after.md`, cùng cấu hình đo với "before":

| Đồng thời | Before: lỗi / p95 / req/s | After (threadpool): lỗi / p95 / req/s |
|---|---|---|
| 1 | 0% / 6.3s / 0.19 | 5% / 6.6s / 0.18 |
| 2 | 0% / 10.9s / 0.20 | 0% / 8.5s / 0.28 |
| 4 | 10% / 42.1s / 0.21 | **0% / 13.3s / 0.37** |
| 8 | 25% / 49.1s / 0.18 | **100% HTTP 502** |

- Dự đoán "throughput không tăng" ở trên **sai**: ở 2–4 đồng thời throughput tăng
  1.4–1.8× và p95 giảm 42s → 13s (Render free vẫn có chút CPU song song). Server p50
  tăng 4.9s → 9.7s ở 4 đồng thời nghĩa là các request đang **chạy song song và chia
  CPU**, không còn xếp hàng nối tiếp.
- Ở 8 đồng thời thì **tệ hơn before**: 20/20 lỗi 502, 8 request đầu lỗi đồng loạt sau
  ~10.3s, các request sau lỗi ngay ~300 ms → process bị kill rồi restart (không phải
  timeout proxy). Giả thuyết hết RAM 512 MB. **Kiểm chứng local** (uvicorn thật, 8
  đồng thời × 24 request, đo peak RSS cả cây tiến trình):

| Cap số ảnh xử lý cùng lúc | Peak RSS, ảnh test 81 KB (740×1159) | Peak RSS, ảnh điện thoại 12 MP | req/s local |
|---|---|---|---|
| không giới hạn | 555 MB | 1032 MB | 21.1 |
| 8 | 566 MB | 905 MB | 20.0 |
| 4 | 433 MB | 714 MB | 21.5 |
| **2 (mặc định mới)** | **362 MB** | **510 MB** | 19.9 |
| 1 | 327 MB | 442 MB | 12.8 |

  Base RSS ~287 MB (ONNX + MediaPipe đã nạp). Mỗi ảnh đang xử lý tốn ~35 MB (ảnh nhỏ)
  tới ~150 MB (12 MP) — vượt 512 MB ngay từ ~6 ảnh nhỏ hoặc 2 ảnh điện thoại. Số Windows,
  Linux trên Render có thể lệch, nhưng cùng bậc.
- **Sửa:** `app/controller.py` thêm `asyncio.Semaphore` quanh `run_in_threadpool`
  (env `MAX_CONCURRENT_PREDICTIONS`, mặc định 2). Request thứ 3 trở đi chờ ở semaphore
  — không giữ thread, không giữ ảnh đã giải mã. Chọn 2 vì giữ gần hết throughput và
  nằm dưới 512 MB với ảnh thường; với ảnh 12 MP vẫn sát ngưỡng → nếu Render log lại
  thấy OOM thì đặt env `MAX_CONCURRENT_PREDICTIONS=1`. Giảm kích thước ảnh trước khi
  suy luận (ảnh 12 MP → ~1280 px) sẽ hạ hẳn peak nhưng phải scale box trả về cho
  web — để lại làm việc sau.
- 1 lỗi 502 lẻ ở mức 1 đồng thời (request thứ 4, sau 5.2s) **chưa giải thích được** — không
  phải OOM (chỉ 1 ảnh đang xử lý); theo dõi ở lần đo 3.
- **Cold start chưa đo được thật:** lần chạy "after" `/health` trả 200 sau 0.3s
  (service đang thức), 7.8s ở `/predict` đầu chỉ là thời gian nạp model lần đầu. Cần
  chạy lại script sau ≥ 15 phút không có traffic.
- Cần **deploy lại + đo lần 3** (cùng cấu hình) để xác nhận cap 2 hết 502 ở 8 đồng thời.

**Smoke test:** `dedup_split` chạy thật trên data thật (2 lần, manifest tái tạo giống
nhau); cell notebook 06 không cần GPU (T12.2, T12.3, `per_image_errors`, OOD) chạy thật
ở local với `best.onnx` thay `best.pt` — bắt được 1 bug (`plot_grid` crash khi chỉ có
1 ảnh lỗi), đã sửa và chạy lại; OOD khớp Giai đoạn 5 (17/18, cùng ảnh sai). Cell train
(T12.5, T12.7) + EigenCAM chỉ kiểm tra cú pháp — cần GPU Colab.

**T12.4 — tập OOD mở rộng (một phần):** 27 ảnh Wikimedia Commons (CC0 / PD / CC BY /
CC BY-SA, ghi công trong `data/ood_samples/commons_sources.csv`), chọn tay sau khi xem
từng ảnh, kiểm trùng với cả 1013 ảnh Roboflow bằng đúng tín hiệu của `dedup_split.py`
(không ảnh nào dHash ≤ 12; 4 ảnh vượt ngưỡng ORB đã xem tận mắt — khớp giả do ảnh scan
nhiễu). Tổng 45 ảnh, 8–10/lớp, đủ 5 lớp. **Còn thiếu ảnh tự chụp điện thoại.**

**T12.3/T12.5–T12.7 — kết quả Colab (2026-11-05, Tesla T4, Ultralytics 8.4.202,
torch 2.11),** output đầy đủ nằm trong `notebooks/06_clean_split_retrain.ipynb`:

*T12.3 — model cũ `yolov8n_v1_baseline`, đo bằng `.pt`:*

| Test gốc | mAP@0.5 | mAP@0.5:0.95 | P | R |
|---|---|---|---|---|
| đủ 101 ảnh (có rò rỉ) | 0.9939 | 0.8333 | 0.9865 | 0.9770 |
| 42 ảnh sạch | 0.9950 | 0.7741 | 0.9640 | 0.9772 |

Khớp kết luận đã đo local bằng ONNX: rò rỉ thổi phồng mAP@0.5:0.95 ~5.9pp và precision
~2.3pp; mAP@0.5 và recall gần như không đổi.

*T12.5 — `yolov8n_v1_clean_baseline`* (50 epoch, batch 16, 0.197 giờ): valid mAP@0.5
0.995 / mAP@0.5:0.95 0.845. **Test mới (154 ảnh, 159 box): mAP@0.5 0.9906, mAP@0.5:0.95
0.8242, P 0.9526, R 0.9872.** Per-class mAP@0.5:0.95: bridge 0.884, downward 0.881,
plank 0.816, shoulderstand 0.789, tree 0.751.

*T12.6 — error analysis:*
- Test, conf 0.5: **7/154 ảnh có lỗi** (5 ảnh gốc; 2 trong số đó có 2 bản lật), **tất cả
  là `shoulderstand`**: 4 bỏ sót, 3 nhầm lớp (2 → bridge, 1 → downward), 2 box thừa.
  Confusion matrix: shoulderstand → bridge 3, shoulderstand → downward 2.
- Theo ảnh: ảnh đồ hoạ/minh hoạ 3/7 (silhouette bị bỏ sót; hình vẽ nằm kê hông, chân
  dựng thẳng bị gọi bridge 0.69/0.89 — nhãn mơ hồ); nhiều người chồng lấn 2/7 (2 người
  bị gộp 1 box; box thừa đè lên người chính); người nhỏ ngược sáng trước cửa sổ 2/7.
- EigenCAM trên ảnh sai: ở ảnh nhiều người, kích hoạt trải trên nền/trần thay vì người;
  ở hình vẽ chỉ một dải hẹp quanh hông, không phủ chân. EigenCAM thô, chỉ là gợi ý.
- **OOD: 37/45 = 82.2%.** 8 ảnh sai: **plank 6/9**, bridge 1/8, tree 1/9. Plank sai do
  side plank (→ tree 0.77, → shoulderstand 0.60), 1 ảnh nhãn plank nhưng người đứng một
  chân tựa tường (→ tree 0.80, **nên xem lại nhãn ảnh OOD này**), và 3 ảnh ngoài trời
  người nhỏ/nhiều người/nền rối (2 không phát hiện, 1 → bridge 0.53). Bridge: ảnh scan
  đen trắng. Tree: người rất nhỏ ở xa.
- Lỗi test (toàn shoulderstand) và lỗi OOD (chủ yếu plank) rơi vào lớp khác nhau → test
  cùng phân bố không đại diện cho lỗi người dùng thật. Pattern chung: người nhỏ/xa, cảnh
  nhiều người, ảnh/biến thể tư thế không có trong train.

*T12.7 — vòng cải tiến:* thay đổi duy nhất `yolov8n.pt` → `yolov8s.pt`
(`OBSERVED_ISSUE = "loose_boxes_bigger_model"`), cùng batch 16, 50 epoch, 0.266 giờ.

| Run | mAP@0.5 (test) | mAP@0.5:0.95 (test) | P | R | Ảnh test có lỗi (conf 0.5) | OOD accuracy | mAP@0.5:0.95 (valid) |
|---|---|---|---|---|---|---|---|
| `yolov8n_v1_clean_baseline` (trước) | 0.9906 | 0.8242 | 0.953 | 0.987 | 7 | 82.2% (37/45) | 0.845 |
| `yolov8n_v1_clean_feedback` (sau) | 0.9883 | 0.8156 | 0.970 | 0.957 | 10 | 71.1% (32/45) | 0.852 |

**Không cải thiện** — kém hơn ở cả 4 chỉ số test/OOD dù valid nhỉnh hơn 0.7pp. Giả thuyết
(chưa kiểm chứng): model ~3.5 lần tham số (11.1M so với 3.1M) khớp quá mức với 703 ảnh
train. Giới hạn: 1 seed, test chỉ 88 nhóm độc lập nên chênh dưới 1pp mAP nằm trong
nhiễu; chênh OOD là 5/45 ảnh. `loose_boxes_bigger_model` là lựa chọn dự phòng, không
nhắm pattern cụ thể nào ở T12.6 (lỗi quan sát được không phải do box lỏng) — nếu làm
thêm vòng 2 thì `small_person` khớp pattern hơn; khi đó báo cáo cả hai vòng, không thay
thế vòng này. **Run thắng: `yolov8n_v1_clean_baseline`** → export ở T12.8.

Ghi chú môi trường: Colab đã lên Python 3.13 nên `mediapipe==0.10.21` không cài được ở
đó — `requirements.txt` thêm marker `python_version < "3.13"` (commit `80ee3fb`). File
`.pt` của cả hai run chỉ nằm trên Drive (`runs/detect/`), chưa có ở local.

**T12.8 — đã export ở local, CHƯA deploy (chờ quyết định):** `models/best.pt`
(`yolov8n_v1_clean_baseline`, xác nhận qua `train_args` trong checkpoint) →
`src/models/export.py::export_onnx()` → `models/best.onnx` (sha256 `42eda24f…`, bản cũ
`be816f0c…`). Kiểm tra bản ONNX mới, CPU:
- Test sạch 154 ảnh: mAP@0.5 0.985, mAP@0.5:0.95 0.765, P 0.958, R 0.966 (`.pt`/GPU trên
  Colab: 0.991 / 0.824 — cùng mức lệch ONNX/CPU so với `.pt` như đã thấy ở T12.3).
- Qua đúng đường chạy của app (`PoseDetectionService.predict_image`) trên 45 ảnh OOD:
  **model mới 37/45 (82.2%, khớp Colab), model cũ đang ở PROD 40/45 (88.9%)**. 3 ảnh
  khác nhau đều là `plank` (cũ đúng, mới → tree / shoulderstand / không phát hiện).
- Giải thích hợp lý (chưa kiểm chứng): model cũ train trên split rò rỉ nên đã thấy gần
  như toàn bộ 552 nhóm ảnh; model mới chỉ thấy 383 nhóm (70%). Điểm test của model cũ
  không tin được, nhưng bản thân model lại học từ nhiều ảnh khác nhau hơn. Chênh 3/45
  ảnh là mẫu nhỏ.
- Hệ quả: thay model mới lên PROD có thể làm người dùng thật nhận kết quả kém hơn một
  chút. Lựa chọn: (a) deploy model mới như spec; (b) giữ model cũ ở PROD, chỉ dùng model
  mới để báo cáo số đo sạch; (c) train thêm bản "final" trên toàn bộ 1013 ảnh với đúng
  config đã được đánh giá, deploy bản đó (không có test set riêng — số báo cáo vẫn là
  của `clean_baseline`).

**Quyết định (2026-11-05): chọn (c).** `models/best.onnx` đã khôi phục về bản cũ (PROD
không đổi cho tới khi có bản final). Thêm `write_all_data_yaml()` trong
`src/data/dedup_split.py` (train = cả 3 split, 1013 ảnh; `val` trỏ vào test chỉ để
Ultralytics chạy được — không phải điểm test) và 2 cell cuối notebook 06: train
`yolov8n_v1_final_alldata` đúng config `clean_baseline`, lấy `last.pt` (không chọn
"best" theo val đã nằm trong train), đo OOD. Deploy bản này **chỉ khi** OOD qua app
không kém model cũ (40/45); nếu kém thì giữ model cũ và ghi đúng như vậy.

**Deferred / cần bạn:** T12.4 phần ảnh điện thoại, T12.8 (export
`yolov8n_v1_clean_baseline` + deploy — export ONNX không cần GPU), T12.10 deploy lại +
đo lần 3 ở 8 đồng thời + đo cold start sau ≥ 15 phút ngủ, T12.11 (docs).
