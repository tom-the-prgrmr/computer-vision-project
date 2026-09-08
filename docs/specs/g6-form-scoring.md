# Spec — g6. Form scoring rule-based (rubric: mục 6 — Phần tự nghĩ thêm)

**Plan source:** `docs/PLAN.md` — Giai đoạn 6
**Status:** implemented

## Mục tiêu

Implement `score_pose()` trong `src/pose_scoring/angle_rules.py` cho đúng
**5 lớp thật** của dataset v1 (`bridge`, `downward`, `plank`,
`shoulderstand`, `tree`), hiệu chỉnh ngưỡng góc (`POSE_RULES`) bằng số đo
thật từ MediaPipe Pose trên ảnh mẫu thật, và test bằng tay để xác nhận
output hợp lý. **Không phải model train, không có accuracy/F1** — chỉ cần
chạy đúng logic + ngưỡng hợp lý theo con mắt thường (`CLAUDE.md`).

## Vấn đề với `POSE_RULES` hiện tại

`POSE_RULES` hiện chỉ có `tree` và `warrior2` (placeholder viết trước khi
chốt dataset). **`warrior2` không phải 1 trong 5 lớp thật của dataset v1**
(xem `docs/problem_statement.md`) — phải bỏ, thay bằng đúng 5 lớp:
`bridge`, `downward`, `plank`, `shoulderstand`, `tree`.

## Việc cụ thể

**T6.1 — Ảnh mẫu "form đúng" (không cần thao tác ngoài môi trường này):**
Tải dataset v1 cục bộ (đã có `ROBOFLOW_API_KEY` trong `.env` — chạy
`scripts/download_data.sh` ngay trong môi trường này, không cần Colab),
chọn 2-3 ảnh rõ nét/đúng tư thế mỗi lớp trong 5 lớp (10-15 ảnh), copy vào
`data/pose_rule_samples/<lop>/*.jpg` (mirror cách làm `data/ood_samples/`
ở Giai đoạn 5 — ảnh nhỏ, có README ghi nguồn). Dùng ảnh từ chính dataset
v1 (không dùng lại ảnh Kaggle OOD của Giai đoạn 5 — đó là tập để đo lỗi
detector ngoài phân bố, mục đích khác, không phải ảnh "chuẩn form" để
hiệu chỉnh góc).

**T6.2 — Đo góc thật để hiệu chỉnh ngưỡng:** Viết `scripts/calibrate_pose_rules.py`
(script chạy 1 lần, không phải notebook — không cần Colab/GPU, MediaPipe
chạy CPU đủ nhanh cho 10-15 ảnh):
- Chạy `mediapipe.solutions.pose.Pose(static_image_mode=True)` trực tiếp
  trên từng ảnh mẫu (ảnh trong dataset đã crop khá sát người tập, không
  cần crop qua YOLO trước — khác với luồng thật ở `app/service.py` sau
  này, nhưng đủ cho mục đích hiệu chỉnh ngưỡng).
- Convert landmark từ toạ độ chuẩn hoá `[0,1]` MediaPipe trả về sang toạ
  độ pixel thật (`x * width`, `y * height`) — **bắt buộc**, vì góc tính
  qua `joint_angle()` không bất biến với scale khác nhau theo trục x/y
  nếu ảnh không vuông (chuẩn hoá theo width/height riêng biệt).
- Với mỗi ảnh, in góc thật cho từng khớp liên quan đến lớp đó (xem danh
  sách khớp per-class ở dưới) để bạn nhìn số thật rồi chốt `min_deg`/
  `max_deg` (cộng biên độ dung sai hợp lý, vd ±10-15°, không chốt đúng y
  hệt số đo được — ảnh mẫu khác sẽ lệch chút).

**Danh sách khớp per-class (thay `POSE_RULES` hiện tại, số độ ở đây chỉ là
ước lượng ban đầu theo kiến thức yoga phổ thông — sẽ chốt lại bằng số đo
thật ở T6.2, không giữ nguyên mù quáng):**

| Lớp | Khớp | Ý nghĩa | Ước lượng ban đầu |
|---|---|---|---|
| `tree` | `standing_knee` | chân trụ duỗi thẳng | 170-180° |
| `tree` | `bent_knee` | chân co gập, đầu gối mở ra ngoài | 20-90° |
| `downward` | `hip` | hông gập tạo hình chữ V ngược | 70-100° |
| `downward` | `knee` | chân duỗi thẳng | 160-180° |
| `downward` | `elbow` | tay duỗi thẳng, đẩy sàn | 160-180° |
| `plank` | `hip` | thân thẳng hàng vai-hông-gối (không võng/gù) | 160-180° |
| `plank` | `elbow` | tay duỗi thẳng (high plank) | 160-180° |
| `shoulderstand` | `hip` | thân thẳng đứng | 160-180° |
| `shoulderstand` | `knee` | chân duỗi thẳng lên trời | 160-180° |
| `bridge` | `hip` | hông nâng lên, gập nhẹ (không thẳng hoàn toàn) | 140-170° |
| `bridge` | `knee` | gối gập vì bàn chân đặt sàn | 70-100° |

`tree` giữ tên khớp có "trái/phải" ngầm định (chân nào co/chân nào
duỗi khác nhau tuỳ người) — `bridge`/`downward`/`plank`/`shoulderstand`
đối xứng nên dùng tên khớp không phân trái/phải (vd `hip`, `knee`,
`elbow`), `score_pose()` tự lấy **trung bình góc trái + phải**.

**T6.3 — Implement `score_pose()`:**
- Thêm `LEFT_WRIST, RIGHT_WRIST = 15, 16` vào danh sách landmark index
  (cần cho khớp `elbow` — hiện file chỉ có tới elbow, chưa có wrist).
- `JOINT_TRIPLETS: dict[str, tuple[int, int, int]]` map tên khớp có
  trái/phải (`"left_knee"`, `"right_hip"`, ...) sang bộ 3 landmark index
  tính góc (vd `"left_knee": (LEFT_HIP, LEFT_KNEE, LEFT_ANKLE)`,
  `"left_hip": (LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE)`, `"left_elbow":
  (LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST)`, tương tự cho `right_*`).
- Hàm nội bộ `_resolve_joint_angle(joint_name, landmarks) -> float`:
  - Tên khớp đối xứng (`"hip"`, `"knee"`, `"elbow"`) → trung bình
    `joint_angle()` của cặp `left_<name>`/`right_<name>`.
  - `"standing_knee"`/`"bent_knee"` (riêng `tree`) → tính cả
    `left_knee`/`right_knee`, góc **lớn hơn** = `standing_knee`, góc
    **nhỏ hơn** = `bent_knee` (không đoán trước chân nào — người tập có
    thể đứng trụ chân trái hoặc phải).
- `score_pose(pose_class, landmarks)`: nếu `pose_class not in POSE_RULES`
  → `FormScore(pose_class, ok=True, issues=[])` ngay (T6.5, không tính
  toán gì thêm). Ngược lại, với mỗi `AngleRange` trong
  `POSE_RULES[pose_class]`: gọi `_resolve_joint_angle()`, so với
  `[min_deg, max_deg]`, ngoài khoảng thì thêm `tip` vào `issues`.
  `ok = len(issues) == 0`.

**T6.4 — Test thủ công (script hoặc cell nhanh, chạy local):**
- Với 2-3 ảnh mẫu T6.1 mỗi lớp (đã coi là "form đúng") → chạy
  `score_pose()`, kỳ vọng đa số `ok=True` (không bắt buộc 100% vì ngưỡng
  có dung sai, ảnh thật luôn hơi lệch — nếu nhiều ảnh "đúng" vẫn bị
  `ok=False` thì ngưỡng T6.2 đang quá chặt, quay lại nới ra).
- **"Ảnh sai" (2/tư thế):** dataset không có ảnh "form sai" gắn nhãn sẵn
  (không tồn tại nguồn thật cho việc này) — dùng **landmark tổng hợp**:
  lấy landmark thật từ 1 ảnh đúng, lệch tay 1 góc ra ngoài ngưỡng (vd
  giảm `standing_knee` xuống 120°) rồi chạy `score_pose()`, kỳ vọng
  `ok=False` với đúng `tip` tương ứng. Đây là test logic (unit-test kiểu
  synthetic edge-case), không phải benchmark ảnh sai thật — ghi rõ điều
  này khi báo cáo, không nhận vơ là "test trên ảnh sai thật".

**T6.5 — Lớp ngoài `POSE_RULES`:** đã gộp vào T6.3 (`ok=True, issues=[]`
ngay khi `pose_class not in POSE_RULES`, không crash).

## File/module liên quan

- `src/pose_scoring/angle_rules.py` — sửa `POSE_RULES` (5 lớp thật),
  thêm `LEFT_WRIST`/`RIGHT_WRIST`, `JOINT_TRIPLETS`, implement
  `score_pose()`
- `scripts/calibrate_pose_rules.py` — mới, script hiệu chỉnh 1 lần
- `data/pose_rule_samples/` — mới, 10-15 ảnh mẫu + README nguồn
- `docs/PLAN.md`, `docs/requirement_checklist.md` (tick khi đóng)

## Bằng chứng / số liệu kỳ vọng

- Output `scripts/calibrate_pose_rules.py`: góc thật đo được mỗi khớp
  mỗi ảnh mẫu (căn cứ để chốt `min_deg`/`max_deg` trong `POSE_RULES`)
- Kết quả T6.4: bảng ảnh đúng → `score_pose()` trả gì (kỳ vọng đa số
  `ok=True`), cộng vài case synthetic lệch góc → trả đúng `issues`

## Cách bạn tự test sau khi tôi xong

Không cần Colab — chạy local (venv của bạn hoặc `.venv` đã có sẵn
`mediapipe`):
```bash
python scripts/calibrate_pose_rules.py   # xem góc thật đo được
python -c "từ script T6.4 mình viết, in kết quả score_pose() trên ảnh mẫu"
```
Mình sẽ đưa lệnh cụ thể khi implement xong. Bạn chỉ cần nhìn output có
hợp lý bằng mắt (ảnh đúng tư thế → phần lớn `ok=True`, ảnh lệch góc tổng
hợp → `ok=False` đúng lý do).

## ❓ Quyết định cần bạn chốt

Không có — toàn bộ việc (tải dataset, chọn ảnh mẫu, hiệu chỉnh góc, code)
làm được trong môi trường này, không cần Colab/GPU/tài khoản ngoài nào
mới. Bảng khớp/ngưỡng ban đầu ở trên là lựa chọn dựa trên kiến thức yoga
phổ thông + sẽ tự hiệu chỉnh lại bằng số đo thật ở T6.2, không cần bạn
chốt trước.

## Rủi ro / điều cần lưu ý

- Không xử lý `visibility` (độ tin cậy) của từng landmark MediaPipe trả
  về — nếu khớp bị che khuất/mất trong ảnh, góc tính ra có thể sai mà
  không có cảnh báo. Biết trước, không xử lý ở bản đầu (rủi ro chấp nhận
  được cho 1 lớp heuristic, không phải model chính).
- Ảnh dataset Roboflow đôi khi có nhiều người/vật thể phụ trong khung —
  MediaPipe Pose (mặc định) chỉ detect 1 người/ảnh, có thể bắt nhầm người
  không phải người tập chính nếu ảnh có 2+ người — chọn ảnh mẫu T6.1 ưu
  tiên ảnh rõ 1 người để tránh vấn đề này (không phải sửa trong code).
- Ngưỡng góc trong bảng trên là suy luận từ kiến thức yoga phổ thông
  (không phải tài liệu y khoa/huấn luyện viên chuyên môn) — đủ dùng cho
  mục đích "phần tự nghĩ thêm" của bài tập, không phải khuyến nghị tập
  luyện thật.
- `plank` trong ảnh dataset có thể là high plank (tay thẳng) hoặc forearm
  plank (chống khuỷu tay) — 2 dạng có ngưỡng `elbow` khác hẳn nhau. Sẽ
  xác nhận qua ảnh mẫu T6.1 thật trước khi chốt ngưỡng, không giả định
  mù quáng là high plank.

## Cập nhật (sau khi implement)

- **`plank` xác nhận đúng như lo ngại:** ảnh mẫu thật cho thấy dataset gộp
  cả high plank (~170-175°) và forearm plank (~90°) vào 1 lớp — đã **bỏ
  rule `elbow` cho `plank`**, chỉ giữ `hip`.
- **MediaPipe Pose kém tin cậy trên tư thế lộn ngược:** 1 ảnh
  `shoulderstand` mẫu ban đầu (nền cát/trời tương phản thấp) cho kết quả
  góc lệch hẳn (hip=96.8° so với ~155-160° ở 2 ảnh cùng lớp) dù đúng tư
  thế khi nhìn bằng mắt — đã thay ảnh khác, không dùng số liệu lệch này
  để hiệu chỉnh ngưỡng. Ghi nhận là hạn chế đã biết của MediaPipe Pose
  với tư thế đầu ở dưới (shoulderstand, có thể cả headstand nếu thêm lớp
  này sau) khi nền/tương phản không thuận lợi.
- **Góc quay camera làm méo góc chiếu 2D (khác nguyên nhân trên):** 1 ảnh
  `plank` (`00000006`, chụp góc chéo 3/4) đo hip=119.8° (trái/phải đồng
  nhất ~118-122, không phải nhiễu detect landmark) trong khi 2 ảnh plank
  thẳng cạnh còn lại đo ~174-179°. Khác case shoulderstand ở trên (đó là
  MediaPipe detect sai landmark) — đây là hạn chế cố hữu của việc tính góc
  hình học từ 1 ảnh đơn không có depth/3D: thân người có thể thẳng thật
  ngoài đời nhưng góc quay nghiêng làm góc chiếu 2D đo được lệch. **Giữ
  nguyên ảnh này** (không thay) làm ví dụ minh hoạ hạn chế, không phải
  loại bỏ dữ liệu bất tiện — `score_pose()` sẽ báo ảnh đó "chưa thẳng
  thân", biết trước và ghi nhận công khai (xem
  `data/pose_rule_samples/README.md`, comment tại
  `POSE_RULES["plank"]`).

## Implementation notes

**Files touched:** `src/pose_scoring/angle_rules.py` (implement
`score_pose()`, 5 lớp thật thay `tree`+`warrior2`), `src/pose_scoring/landmark_extraction.py`
(mới — tách MediaPipe I/O ra khỏi angle_rules.py để `app/service.py` dùng
lại được ở Giai đoạn 7, không lặp code), `scripts/calibrate_pose_rules.py`
(mới), `scripts/manual_test_score_pose.py` (mới), `data/pose_rule_samples/`
(mới, 15 ảnh thật + README), `requirements.txt` (pin `mediapipe==0.10.21`).

**Vấn đề môi trường thật gặp phải:** `pip install mediapipe>=0.10` cài
bản `1.0.1` — mediapipe 1.0 bỏ hẳn `mediapipe.solutions.pose` (API cổ
điển) chuyển sang Tasks API cần tải `.task` model asset riêng. Phát hiện
qua `AttributeError: module 'mediapipe' has no attribute 'solutions'`
khi chạy calibration script thật. Sửa bằng pin `mediapipe==0.10.21`
(bản cuối còn API cũ) trong `requirements.txt` — áp dụng cho mọi môi
trường cài từ file này (kể cả Colab sau này nếu dùng `_extract_landmarks()`
ở Giai đoạn 7).

**T6.1 — Ảnh mẫu:** tải dataset v1 cục bộ (đã có `ROBOFLOW_API_KEY`,
không cần Colab), chọn 15 ảnh (3/lớp × 5 lớp) từ ảnh chỉ có 1 bbox. Lần
chọn đầu bị `code-review` bắt lỗi: 2 lớp (`tree`, `shoulderstand`) vô
tình chọn trùng 2 ảnh cùng nguồn gốc Roboflow (khác hash hậu tố `.rf.`,
cùng ảnh gốc) — sửa bằng dedup theo tên file gốc, quét cả 3 split.

**T6.2 — Hiệu chỉnh:** chạy `calibrate_pose_rules.py`, dùng số đo thật
±15° làm `POSE_RULES`. 2 phát hiện quan trọng trong lúc hiệu chỉnh (xem
chi tiết ở mục "Cập nhật" trên và `data/pose_rule_samples/README.md`):
(1) `plank` trong dataset gộp cả high plank và forearm plank → bỏ rule
`elbow`, chỉ giữ `hip`; (2) 2 hạn chế đo góc khác nguyên nhân — MediaPipe
detect sai landmark trên tư thế lộn ngược nền khó (shoulderstand, đã
thay ảnh), và góc quay camera làm méo góc chiếu 2D (plank, giữ ảnh làm
ví dụ minh hoạ hạn chế).

**T6.3 — `score_pose()`:** implement theo thiết kế trong spec (`JOINT_TRIPLETS`,
`resolve_joint_angle()` gộp trái/phải hoặc chọn động cho `tree`). T6.5
(lớp ngoài `POSE_RULES` → `ok=True`) gộp vào cùng hàm.

**T6.4 — Test:** `manual_test_score_pose.py` — 14/15 ảnh mẫu thật
`ok=True` (1 ảnh "sai" đã biết lý do, xem trên); 5/5 case landmark tổng
hợp (chủ động lệch góc) phát hiện đúng issue kỳ vọng.

**Review:** `cv-architecture-review` 2 lượt + 1 lần tự kiểm tra thủ công
(không lặp agent lần 3 theo đúng quy tắc skill). Lượt 1: sạch kiến trúc.
`code-review` (medium): bắt lỗi trùng ảnh mẫu nguồn (đã sửa). Lượt 2
(sau khi sửa ảnh trùng): phát hiện ngưỡng `plank.hip` không khớp
methodology "±15° từ số đo thật" đã ghi trong comment (âm thầm bỏ 1 mẫu
outlier không giải thích) — đã sửa bằng cách ghi rõ lý do outlier (góc
quay camera, không phải lỗi detect) thay vì đổi số tuỳ tiện; xác nhận lại
bằng smoke test không đổi kết quả (vẫn 14/15 + 5/5).

**Deferred:** không có — mọi việc trong T6.1-T6.5 làm được và đã làm
xong trong môi trường này, không cần Colab/GPU.
