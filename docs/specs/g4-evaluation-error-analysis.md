# Spec — G4. Evaluation & Error Analysis (rubric: mục 4 — Evaluation & Error Analysis)

**Plan source:** `docs/PLAN.md` — Giai đoạn 4 (`T4.1`–`T4.5`)
**Status:** implemented <!-- code xong — chạy thật trên Colab + T4.5 tóm tắt còn deferred, xem Implementation notes -->

## Mục tiêu

Phân tích lỗi của model baseline (config ON đã chốt ở Giai đoạn 3 —
`runs/detect/yolov8n_v1_baseline/weights/best.pt`): xác định cặp lớp hay bị
nhầm nhất qua confusion matrix, trực quan hoá vùng model "nhìn" bằng EigenCAM
(không dùng Grad-CAM chuẩn — không áp dụng thẳng được cho detection, xem
`docs/REQUIREMENTS.md` mục 7), và tóm tắt pattern lỗi lặp lại. Đây là bằng
chứng bắt buộc cho rubric mục 4, đồng thời là input cho Giai đoạn 5
(feedback loop — chọn hướng cải thiện dựa trên lỗi tìm thấy ở đây).

## Việc cụ thể

- **T4.1 — Helper confusion matrix trong `src/evaluation/metrics.py`**
  Ultralytics tự lưu ảnh `confusion_matrix.png` khi `.val()` chạy, nhưng
  không expose sẵn "top confused pairs" dạng số — viết 2 hàm:
  ```python
  def load_confusion_matrix(model_path: str, data_yaml: str) -> tuple[np.ndarray, list[str]]:
      """Chạy model.val(), trả về (ma trận (nc+1)x(nc+1) gồm cả hàng/cột
      background, danh sách tên lớp + 'background' cuối cùng)."""

  def top_confused_pairs(
      matrix: np.ndarray, class_names: list[str], k: int = 3
  ) -> list[tuple[str, str, int]]:
      """Trả về top-k cặp (lớp_thật, lớp_dự_đoán, số_lần) ngoài đường chéo,
      sắp giảm dần theo số lần — bỏ qua đường chéo (dự đoán đúng) và các
      cặp liên quan tới 'background' nếu muốn tập trung vào nhầm lẫn giữa
      các tư thế thật (tham số `exclude_background: bool = True`)."""
  ```
  Acceptance: 2 hàm import được, chạy trên `best.pt` + `data.yaml` thật trả
  về ma trận đúng shape (6×6 cho 5 lớp + background) và danh sách cặp hợp
  lý (không lỗi index).

- **T4.2 — Xác định cặp lớp hay nhầm nhất**
  Gọi `top_confused_pairs(..., k=3)` trong notebook, in kết quả.
  Acceptance: notebook in ra tối đa 3 cặp lớp thật kèm số lần nhầm — nếu
  model gần như hoàn hảo (mAP baseline đã 0.99) có thể chỉ có 1-2 cặp có
  giá trị > 0, ghi nhận đúng thực tế đó thay vì ép đủ 3.

- **T4.3 — EigenCAM**
  `pytorch-grad-cam` đã có trong `requirements.txt` (`grad-cam`, import
  `from pytorch_grad_cam import EigenCAM`). Load `best.pt` qua
  `ultralytics.YOLO`, lấy `model.model` (`nn.Module` PyTorch bên trong) làm
  target, chọn **target layer cuối backbone/neck ngay trước `Detect` head**
  — in `model.model.model` ra để xem cấu trúc thật rồi chọn index cụ thể
  (thường là `model.model.model[-2]`, nhưng xác nhận bằng cách nhìn tên
  layer thay vì đoán mù). Chạy EigenCAM trên ảnh từ `data/raw/yoga_v1/test/`
  (test set, chưa dùng để train).
  Acceptance: chạy được trên ít nhất 1 ảnh không lỗi, heatmap overlay lên
  ảnh gốc hiển thị được trong notebook.

- **T4.4 — Lưu 3-5 ảnh EigenCAM kèm giải thích**
  Chọn ảnh mẫu theo 2 nhóm: (a) 1-2 ảnh từ cặp lớp hay nhầm nhất ở T4.2
  (nếu có), (b) 2-3 ảnh dự đoán đúng ở các lớp khác nhau — so sánh model
  "nhìn" đúng chỗ (vùng học viên) hay bị phân tâm bởi nền/vật thể khác.
  Acceptance: 3-5 ảnh hiển thị trong notebook, mỗi ảnh có 1-2 câu nhận xét
  ngay dưới (markdown hoặc `plt.title`).

- **T4.5 — Tóm tắt pattern lỗi**
  Từ T4.2 + T4.4, viết đoạn tóm tắt: lớp nào hay nhầm với lớp nào, và giả
  thuyết vì sao (dáng giống nhau, vật nhỏ/bị che khuất, ánh sáng, nền phân
  tâm...). Đây là input trực tiếp cho T5.1 (chọn hướng cải thiện ở Giai
  đoạn 5) nên cần đủ cụ thể để hành động được, không chỉ mô tả chung chung.
  Acceptance: đoạn tóm tắt trong notebook, đủ cụ thể để Giai đoạn 5 dùng
  trực tiếp (tên lớp cụ thể, không chỉ "một số lớp bị nhầm").

## File/module liên quan

- `src/evaluation/metrics.py` — **mới**, implement thật (không stub, tương
  tự `train.py` — 2 hàm thuần logic, không cần thiết kế phức tạp).
- `notebooks/03_evaluation_error_analysis.ipynb` — **mới**, theo đúng
  pattern Setup (mount Drive + cd) + git pull + cài deps ở đầu như 2
  notebook trước.
- Không sửa `src/models/train.py`, `app/`, `src/pose_scoring/` — giai đoạn
  này thuần đánh giá, không train lại, không đụng lớp rule-based (rubric
  mục 4 tách biệt với mục 6).

## Bằng chứng / số liệu kỳ vọng

- Confusion matrix (số liệu thật) + tối đa 3 cặp lớp hay nhầm nhất.
- 3-5 ảnh EigenCAM kèm giải thích.
- 1 đoạn tóm tắt pattern lỗi cụ thể, dùng được cho Giai đoạn 5.

## Cách bạn tự test sau khi tôi xong

1. Trên Colab, mở `03_evaluation_error_analysis.ipynb`, chạy Setup + git
   pull + cài deps (giống 2 notebook trước).
2. Chạy các cell T4.1–T4.5 — cần `runs/detect/yolov8n_v1_baseline/weights/
   best.pt` đã có sẵn trên Drive từ Giai đoạn 2/3 (không train lại).
3. Xem confusion matrix + ảnh EigenCAM hiển thị hợp lý (heatmap tập trung
   vào vùng học viên, không lệch hẳn ra nền) — nếu heatmap trông vô nghĩa
   (toàn bộ ảnh sáng đều hoặc tập trung góc ảnh không liên quan), có thể
   cần đổi lại target layer (T4.3), báo mình để chỉnh.
4. Gửi lại: danh sách cặp lớp hay nhầm (nếu có) + nhận xét của bạn khi
   nhìn ảnh EigenCAM (model nhìn đúng chỗ không) — mình viết tóm tắt cuối
   cùng (T4.5) dựa trên quan sát thật của bạn, không tự suy diễn.

## ❓ Quyết định cần bạn chốt

Không có quyết định mơ hồ cần hỏi trước — target layer cụ thể cho EigenCAM
(T4.3) là chi tiết kỹ thuật xác định bằng cách in cấu trúc model lúc
implement, không phải lựa chọn cần bạn quyết trước.

## Rủi ro / điều cần lưu ý

- mAP baseline đã rất cao (0.99/0.83) — confusion matrix có thể gần như
  hoàn hảo (rất ít off-diagonal), khiến T4.2 không tìm được đủ 3 cặp nhầm
  "thật". Đây là kết quả hợp lệ (dataset v1 dễ), không phải lỗi — nếu xảy
  ra, T4.4/T4.5 sẽ tập trung vào phân tích ảnh đúng + 1-2 ca nhầm ít ỏi tìm
  được, thay vì ép tìm lỗi không tồn tại.
- EigenCAM cho detection (nhiều box/lớp cùng lúc) có thể cho heatmap "mờ"
  hơn so với dùng cho classifier đơn lớp — đây là hạn chế đã biết của kỹ
  thuật, không phải bug, cần nói rõ trong nhận xét thay vì coi là lỗi cần
  sửa.
- Không thể chạy EigenCAM/confusion matrix thật trong môi trường CLI này
  (cần GPU + checkpoint + dataset thật trên Drive) — smoke test chỉ ở mức
  cú pháp/import cho 2 hàm trong `metrics.py` với dữ liệu giả lập.

## Implementation notes

- **Code (`src/evaluation/metrics.py` + `notebooks/03_evaluation_error_analysis.ipynb`) — done.**
  `metrics.py`: `load_confusion_matrix()` (chạy `model.val()`, trả ma trận +
  tên lớp), `top_confused_pairs()` (xếp hạng cặp lớp hay nhầm, loại
  background). Notebook: Setup/git-pull/cài-deps (giống 2 notebook trước) →
  T4.1-T4.2 (gọi 2 hàm trên) → T4.3 (in cấu trúc model để chọn target layer
  EigenCAM, mặc định `-2`, có hướng dẫn đổi nếu heatmap vô nghĩa) → T4.4
  (chạy `predict()` trên toàn bộ test set, tách đúng/sai, chọn 3-5 ảnh ưu
  tiên cặp nhầm nhiều nhất, overlay EigenCAM) → T4.5 placeholder.
  - Review: `cv-architecture-review` 2 lần + `code-review` (medium).
    1 finding thật ở lần đầu (không phải style): **`Confusion Matrix`
    của Ultralytics index theo `[predicted_class, true_class]`** (hàng =
    dự đoán, cột = ground truth — xác nhận qua chính code `plot()` của
    Ultralytics, trục x label "True", trục y label "Predicted"), nhưng code
    ban đầu giả định ngược lại `[true, predicted]` → mọi cặp nhầm sẽ bị in
    **đảo ngược thật/dự đoán** (vd in "Warrior2 -> Tree" trong khi thực tế
    model nhầm Tree thành Warrior2). Đã sửa: cập nhật docstring
    `load_confusion_matrix()` + đổi thứ tự index trong
    `top_confused_pairs()` sang `matrix[pred_idx, true_idx]`. Lần review
    thứ 2 xác nhận sạch.
  - Smoke test: `py_compile` qua `metrics.py`; **tự dựng ma trận giả lập
    với thứ tự index đã biết trước** (predicted=plank khi true=tree, 5
    lần) và gọi `top_confused_pairs()` thật trong `.venv` — xác nhận trả
    về đúng `('tree', 'plank', 5)`, không bị đảo ngược sau khi sửa. JSON +
    cú pháp notebook hợp lệ. Không chạy EigenCAM/`model.val()` thật (cần
    GPU + checkpoint + dataset trên Drive).
- **T4.1-T4.5 (chạy thật trên Colab) — deferred.** Cần bạn tự chạy
  `03_evaluation_error_analysis.ipynb` trên Colab, xem "Cách bạn tự test"
  ở trên, rồi gửi lại quan sát (cặp lớp hay nhầm nếu có, nhận xét ảnh
  EigenCAM) để mình viết tóm tắt T4.5.
