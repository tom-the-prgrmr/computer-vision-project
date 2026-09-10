# Problem Statement

## Bài toán
Phát hiện và phân loại động tác (tư thế) yoga của học viên trong ảnh/video, sau đó
chấm điểm độ chính xác của form và đưa ra gợi ý cải thiện.

## Requirement đã chốt

| # | Yêu cầu | Đáp ứng bằng |
|---|---|---|
| 1 | Train 1 model nhận diện học viên tập yoga **trên video** | YOLOv8 chạy inference theo từng frame video (xem "Xử lý video" bên dưới) — chỉ 1 model duy nhất, không tách riêng model detect người |
| 2 | Detect vùng nào là người tập | Output bounding box của YOLOv8 (localization) |
| 3 | Phân loại động tác | Output class của YOLOv8 (mỗi lớp = 1 tư thế) — cùng 1 forward pass với #2, không phải model riêng |
| 4 | Gán nhãn đúng/sai | Lớp rule-based `src/pose_scoring/angle_rules.py`: MediaPipe Pose (pretrained) trích khớp trong box đã detect → so góc với ngưỡng chuẩn → `form_ok: true/false` |
| 5 | Đưa ra phương án cải thiện | Cùng lớp rule-based ở #4, sinh `tips` theo khớp nào lệch ngưỡng (vd "duỗi thẳng chân trụ hơn") |

**1 model train duy nhất** = YOLOv8 detection (đáp ứng #1-#3 trong cùng 1 lần
infer/frame). #4-#5 là logic rule-based nối tiếp sau, không phải model thứ 2 cần
train — giữ đúng scope "1 trong 3 dạng bài toán đã học" của đề bài.

## Xử lý video
`app/main.py` cần thêm đường xử lý video (ngoài `/predict` ảnh đơn hiện có):
đọc video theo frame (OpenCV `VideoCapture`), chạy YOLOv8 + rule-based scoring
trên từng frame, ghi/stream kết quả (bounding box + tư thế + đúng/sai + tip) đè
lên video output hoặc trả về dạng JSON theo từng frame. Có thể thêm tracking đơn
giản (vd ByteTrack tích hợp sẵn trong Ultralytics — `model.track()`) để giữ ID
học viên ổn định qua các frame và làm mượt kết quả (tránh nhấp nháy đổi tư thế
liên tục do model dự đoán sai lệch ở vài frame lẻ) — coi đây là điểm cộng, không
bắt buộc cho bản đầu tiên chạy được.

## Ai dùng, dùng để làm gì
Người tự tập yoga tại nhà (không có huấn luyện viên trực tiếp kiểm tra form), hoặc
huấn luyện viên muốn giám sát nhiều học viên cùng lúc qua camera lớp học. Sản phẩm
giúp phát hiện học viên đang tập tư thế nào và cảnh báo lỗi form phổ biến theo thời
gian thực.

## Kiến trúc 2 lớp

1. **Model chính (trainable) — Object Detection**
   YOLOv8 fine-tune trên ảnh yoga, mỗi lớp = 1 tư thế (Bridge, Downward Dog, Plank,
   Shoulderstand, Tree, ...). Model vừa khoanh vùng học viên (localization) vừa
   phân loại tư thế (classification) trong một bước — đáp ứng đúng 1 trong 3 dạng
   bài toán đã học (object detection), xử lý được khung hình có nhiều học viên.

2. **Lớp chấm điểm form (mục 6 — phần tự nghĩ thêm, không tự train)**
   Dùng MediaPipe Pose (pretrained) trích 33 keypoint trên vùng học viên đã detect
   → tính góc các khớp chính (khuỷu tay, đầu gối, hông, vai...) → so với ngưỡng góc
   chuẩn của từng tư thế → xuất điểm form + gợi ý cải thiện bằng rule-based logic.

   Lưu ý: đây là feedback cho *người dùng cuối*, khác với mục 5 "Feedback loop –
   cải tiến" (vốn là cải tiến *model detection* dựa trên phân tích lỗi — xem
   `docs/requirement_checklist.md` mục 5).

## Metric thành công
- Model detection: mAP@0.5, mAP@0.5:0.95, per-class precision/recall, confusion
  giữa các cặp tư thế dễ nhầm (vd Warrior I vs Warrior II).
- Lớp chấm điểm form: không có ground-truth "đúng/sai" chuẩn hoá — đánh giá định
  tính bằng cách đối chiếu thủ công một số case, không tính vào metric chính của
  bài (vì đây là phần rule-based, không phải model tự train).
- Deployment: latency/FPS khi serve qua FastAPI (đo trước/sau export ONNX, và
  trước/sau quantization nếu có GPU server).

## Dataset

| Giai đoạn | Nguồn | Số lớp | Ghi chú |
|---|---|---|---|
| v1 (an toàn deadline) | [YOLO YOGA Dataset – Roboflow Universe](https://universe.roboflow.com/object-detection-dt-wzpc6/yolo-yoga-dataset) | 5 (Bridge, Downward Dog, Plank, Shoulderstand, Tree) | Có sẵn bounding box, format YOLO, 1013 ảnh (xác nhận thật, xem chi tiết bên dưới) |
| v2 (nếu có GPU server) | Yoga-82 (classification) + bootstrap bbox bằng pretrained person detector | 15–20 | Xem `src/data/bootstrap_bbox.py` |

So sánh v1 → v2 (thêm lớp, thêm dữ liệu) chính là câu chuyện cho mục 5 (Feedback
loop – cải tiến), có số liệu mAP trước/sau rõ ràng.

### v1 — số liệu thực tế (chạy `notebooks/01_data_exploration.ipynb` trên Colab)

**Số ảnh mỗi split:**

| Split | Số ảnh |
|---|---|
| train | 709 |
| valid | 203 |
| test | 101 |
| **Tổng** | **1013** |

**Phân bố bbox theo lớp** (gộp cả 3 split; nhãn gốc trong `data.yaml` có tiền tố
`yoga-pose `, đã bỏ cho gọn):

| Lớp | Số bbox |
|---|---|
| downward (Downward Dog) | 248 |
| tree | 216 |
| shoulderstand | 206 |
| plank | 195 |
| bridge | 158 |

Tổng 1023 bbox trên 1013 ảnh (~10 ảnh có nhiều hơn 1 học viên/box). Imbalance
**nhẹ** — tỉ lệ lớp nhiều nhất/ít nhất ≈ 1.57× (248/158), không cần
oversampling/class-weight ở baseline; `bridge` là lớp ít ảnh nhất nên nếu
confusion matrix sau này (Giai đoạn 4) cho thấy `bridge` bị nhầm nhiều, đây là
nghi phạm đầu tiên.

**Sanity-check bbox** (10 ảnh mẫu, 2 ảnh/lớp — xem notebook T1.4): đa số bbox
khớp đúng vị trí học viên. Phát hiện 1 trường hợp lệch: 1 ảnh `shoulderstand`
(ảnh minh hoạ nền chữ, không phải ảnh chụp thật) có bbox hẹp hơn tư thế thực
tế, không bao trọn người trong ảnh — ghi nhận là nhiễu nhãn có thể có trong
tập Roboflow, không sửa tay ở bước này (số lượng nhỏ, không đáng kể so với
1013 ảnh), nhưng cần nhớ lại nếu sau này error analysis (Giai đoạn 4) thấy lớp
`shoulderstand` có vấn đề bbox.

**Augmentation đã chốt** (dùng cho `train()` ở Giai đoạn 2):
`flipud=0.0` (tắt — lật dọc làm tư thế yoga vô nghĩa), `fliplr=0.5` (giữ — đối
xứng trái/phải an toàn), `degrees=10` (giới hạn thấp — xoay mạnh làm sai lệch
bbox lẫn góc khớp có ý nghĩa cho lớp rule-based sau này). Không chỉnh lại sau
khi xem ảnh T1.4 — ảnh gốc đã đủ đa dạng góc chụp.

## Training baseline (Giai đoạn 2)

`yolov8n.pt`, `seed=42`, `epochs=50`, `imgsz=640`, augmentation như trên.
Kết quả (Colab, T4 GPU): **mAP@0.5 = 0.9922, mAP@0.5:0.95 = 0.8352**. Rất
cao cho baseline — dataset v1 tương đối "dễ" (5 lớp phân biệt rõ hình dạng
tư thế, học viên thường chiếm phần lớn khung hình).

## Ablation (Giai đoạn 3)

Biến duy nhất thay đổi: **augmentation** (ON = baseline ở trên; OFF = tắt
toàn bộ augmentation — mosaic, hsv, flip, rotate, translate, scale, shear,
perspective, mixup, copy_paste, erasing), giữ nguyên `model`/`seed`/
`epochs`/`imgsz` — xem `docs/specs/g3-ablation.md`.

| Run | mAP@0.5 | mAP@0.5:0.95 | Thời gian train (s) |
|---|---|---|---|
| ON (baseline) | 0.9922 | 0.8352 | 913.2 |
| OFF (no aug) | 0.9754 | 0.8558 | 672.1 |

**Kết luận:** Kết quả trái chiều — ON thắng mAP@0.5 (+1.7pp), OFF thắng
mAP@0.5:0.95 (+2.1pp) và train nhanh hơn ~26%. Không bên nào vượt trội rõ
rệt, nên **chọn augmentation ON làm config chính thức** — lý do: mục tiêu
triển khai thực tế là ảnh/video thật ngoài dataset (camera điện thoại, góc
chụp/ánh sáng đa dạng hơn tập train), augmentation giúp tổng quát hoá tốt
hơn dù không thắng tuyệt đối trên test set cùng phân bố. Dùng config này
cho Giai đoạn 5 (retrain sau cải tiến).

*(mAP baseline ở bảng này lệch nhẹ so với con số train lần đầu — 0.9923/
0.8435 — dù cùng `seed=42`, do YOLO/cuDNN không hoàn toàn deterministic
giữa các lần train trên GPU; chênh lệch ở mức nhiễu bình thường.)*

## Evaluation & Error Analysis (Giai đoạn 4)

Confusion matrix + EigenCAM trên model baseline (config ON,
`yolov8n_v1_baseline`) — xem `docs/specs/g4-evaluation-error-analysis.md`.

**Confusion matrix:** không có cặp lớp nào bị nhầm trên test set (101 ảnh)
— khớp với mAP@0.5 = 0.9922 đã rất cao. 5 ảnh minh hoạ EigenCAM đều là dự
đoán đúng, confidence 0.88–0.96.

**EigenCAM:** ở `tree`, `plank`, `shoulderstand`, vùng model chú ý (heatmap
nóng) tập trung đúng vào phần thân thể đặc trưng cho tư thế (chân co/bàn
chân ở `tree`, vùng hông-thân ở `plank`/`shoulderstand`). Ở `downward` và
`bridge`, vùng nóng lại lan ra rìa khung hình thay vì tập trung hẳn vào
người — không phải model nhầm lẫn thật (confidence vẫn cao, 0.92/0.96) mà
là hạn chế kỹ thuật đã biết của EigenCAM trên model detection (không dùng
Grad-CAM chuẩn được — xem `docs/REQUIREMENTS.md` §7).

**Kết luận:** dataset v1 (5 lớp, hình dạng tư thế khác biệt rõ rệt) quá
"dễ" với `yolov8n` ở baseline — không có pattern lỗi phân loại thật sự để
sửa. Vì vậy hướng cải thiện mặc định ở Giai đoạn 5 (augmentation/
oversampling nhắm đúng cặp lớp hay nhầm) **không áp dụng được** — Giai
đoạn 5 cần chọn hướng khác (vd mở rộng sang v2 nhiều lớp hơn để có bài
toán thật sự khó hơn, hoặc test model trên ảnh/video ngoài dataset để tìm
lỗi thực tế thay vì trên test set cùng phân bố).

## Feedback loop cải tiến (Giai đoạn 5)

Vì Giai đoạn 4 không tìm ra cặp lớp bị nhầm nào, hướng cải thiện chuyển
sang đo lỗi thật trên ảnh **ngoài phân bố dataset Roboflow** (OOD) — xem
`docs/specs/g5-feedback-loop.md`.

**Tập OOD:** 18 ảnh (6/lớp × `downdog`→`downward`, `plank`, `tree`) từ
[niharika41298/yoga-poses-dataset](https://www.kaggle.com/datasets/niharika41298/yoga-poses-dataset)
trên Kaggle — khác hoàn toàn nguồn Roboflow (khác số ảnh, khác 2 lớp
`bridge`/`shoulderstand`, khác phong cách chụp/background).

**Kết quả (chạy thật trên Colab, model `yolov8n_v1_baseline`):**
OOD accuracy = **17/18 = 94.4%**. Đúng 1 lỗi: `plank` bị đoán thành
`tree` (conf 0.82) trên 1 ảnh mà tư thế trong ảnh không giống plank kinh
điển — khả năng cao là nhãn gốc của dataset Kaggle không chuẩn, không
phải lỗi hệ thống của model.

*(Lưu ý: lần chạy đầu trên Colab báo nhầm 0/18 = 0.0% do 1 bug trong code
so sánh — `result.names` của model có tiền tố `"yoga-pose "` chưa được bỏ
trước khi so với nhãn thật. Đã sửa và verify lại bằng cách đối chiếu tay
log gốc + smoke test logic, không phải số liệu suy đoán.)*

**Kết luận:** 94.4% vượt ngưỡng robust đã chốt trước (≥90%), và lỗi duy
nhất không khớp pattern lỗi hệ thống nào (không do ảnh tối/người nhỏ/nền
lộn xộn/mờ) → **không retrain**. Baseline (`yolov8n_v1_baseline`, config
ON từ Giai đoạn 3) đã đủ robust trên mức OOD nhỏ đã kiểm tra. Giới hạn:
tập OOD chỉ 18 ảnh, 3/5 lớp — không phải benchmark thống kê chắc chắn,
chỉ đủ làm bằng chứng định tính cho quyết định này.

## Form scoring rule-based (Giai đoạn 6)

Lớp chấm điểm form — "ý tưởng riêng" của đề bài (rubric mục 6), **không
phải model train được**, không có accuracy/F1 của chính nó — xem
`docs/specs/g6-form-scoring.md` và `CLAUDE.md` về ranh giới với mục 5.

**Hiệu chỉnh ngưỡng bằng số đo thật:** chạy MediaPipe Pose trên 15 ảnh mẫu
thật (3 ảnh/lớp × 5 lớp: `bridge`, `downward`, `plank`, `shoulderstand`,
`tree`, chọn lọc từ dataset v1, dedup theo ảnh gốc Roboflow), đo góc khớp
thật rồi lấy khoảng ±15° làm `POSE_RULES` (thay vì đoán ngưỡng).

**2 hạn chế thật phát hiện trong lúc hiệu chỉnh** (ghi công khai, không
giấu):
- **MediaPipe Pose kém tin cậy trên tư thế lộn ngược, nền tương phản
  thấp:** 1 ảnh `shoulderstand` mẫu ban đầu cho góc lệch hẳn (hip=96.8°
  so với ~155-160° ở 2 ảnh cùng lớp) dù tư thế đúng khi nhìn bằng mắt —
  MediaPipe detect sai landmark, không dùng ảnh này để hiệu chỉnh.
- **Góc quay camera làm méo góc chiếu 2D:** 1 ảnh `plank` chụp góc chéo
  3/4 đo hip=119.8° (trái/phải đồng nhất, không phải nhiễu detect) trong
  khi 2 ảnh plank thẳng cạnh đo ~174-179° — hạn chế cố hữu của tính góc
  hình học từ ảnh đơn không có depth. Giữ nguyên ảnh này làm ví dụ minh
  hoạ hạn chế thay vì loại bỏ dữ liệu bất tiện.
- Dataset gộp cả *high plank* và *forearm plank* vào chung 1 lớp `plank`
  → đã bỏ rule góc khuỷu tay (`elbow`) cho lớp này, chỉ giữ `hip`.

**Kết quả test thủ công:** 14/15 ảnh mẫu thật `ok=True` đúng kỳ vọng (1
ảnh "sai" đã biết lý do — case góc quay camera ở trên); 5/5 case landmark
tổng hợp (chủ động lệch góc) phát hiện đúng issue kỳ vọng.

**Xử lý pose ngoài `POSE_RULES`:** trả `ok=True, issues=[]` thay vì crash
(lớp chưa hiệu chỉnh không nên bị coi là sai form).

## Export & Backend (Giai đoạn 7)

Export `yolov8n_v1_baseline` (config ON, model tốt nhất vì Giai đoạn 5
không retrain) sang ONNX, benchmark latency, wire vào `app/service.py` —
xem `docs/specs/g7-export-backend.md`.

**Benchmark latency (chạy thật trên Colab, GPU T4, N=50 lần inference):**

| Backend | avg latency (ms) | FPS |
|---|---|---|
| PyTorch (.pt) | 247.94 | 4.03 |
| ONNX Runtime (.onnx) | 206.29 | 4.85 |

ONNX nhanh hơn PyTorch ~17%. Cả 2 số đo trên GPU T4 dùng chung của Colab
free-tier, **không đại diện cho CPU thật lúc deploy** — số CPU thật đo
được ở Giai đoạn 9 (xem mục dưới): ~245.8ms local, ~4.5-8.4s trên Render
free tier (CPU bị giới hạn mạnh, không phải bug).

**Backend (`app/service.py`):** implement thật ONNX inference (letterbox
preprocess, NMS theo từng lớp riêng, dịch box về ảnh gốc —
`src/models/onnx_inference.py`) + MediaPipe landmark extraction, nối với
`score_pose()` từ Giai đoạn 6.

**Test end-to-end thật** (CPU local, `best.onnx` thật, `curl` →
`POST /predict` với 1 ảnh `tree`):
```json
{"detections":[{"pose":"tree","confidence":0.92,"box":[256.2,73.5,449.1,592.7],
  "form_ok":true,"tips":[],"latency_ms":245.8}]}
```
Đúng lớp, confidence cao, `form_ok=true` (không có issue) — xác nhận cả 2
lớp (detector ONNX + rule-based form scoring) hoạt động đúng thật, không
chỉ là smoke test với model giả nữa.

## Web demo & Deploy public (Giai đoạn 8-9)

Web demo (`web/index.html`, tab Upload/Camera) đã có sẵn từ trước, Giai
đoạn 8 là verify thật với backend thật (không viết mới) — xem
`docs/specs/g8-web-demo.md`. Giai đoạn 9 deploy public — xem
`docs/specs/g9-deploy-public.md`.

**Kiến trúc deploy thật:** backend FastAPI trên **Render**
(`https://computer-vision-project-hl82.onrender.com`, Docker, free tier,
build từ `Dockerfile`), frontend tĩnh trên **Cloudflare Pages**
(`https://computer-vision-project.pthieu290998.workers.dev`, trỏ vào
`web/`) — 2 origin khác nhau, CORS qua env `ALLOWED_ORIGINS`. Lịch sử đổi
host 2 lần (Hugging Face Spaces → VPS riêng → Render/Cloudflare Pages) do
thông tin thật phát sinh khi thao tác thật (HF Docker Space bắt trả phí
giữa chừng) — chi tiết đầy đủ trong `docs/specs/g9-deploy-public.md`.
Phương án VPS + Caddy vẫn giữ trong repo làm phương án thay thế.

**3 bug thật gặp khi deploy, đều đã sửa và verify lại:**
1. `mediapipe==0.10.21` không có wheel cho Python 3.14 — do Render lúc
   đầu build bằng native Python runtime thay vì `Dockerfile` (chọn nhầm
   Environment lúc tạo service) — sửa bằng chọn đúng `Docker` runtime.
2. `ImportError: libGL.so.1` lúc import `cv2` trên container Linux —
   `opencv-python-headless` vẫn cần thư viện đồ hoạ hệ thống dù là bản
   "headless" — sửa bằng thêm `apt-get install libgl1 libglib2.0-0` vào
   `Dockerfile`.
3. **Camera trên iPhone Safari bị đẩy vào native fullscreen video player**
   (UI Live/Picture-in-Picture/pause che mất canvas overlay) thay vì phát
   inline — bug WebKit đã biết với nguồn `getUserMedia`; `playsinline`
   chuẩn không đủ — sửa bằng thêm `webkit-playsinline` + set
   `playsInline`/`muted` qua thuộc tính JS trước khi gán `srcObject`.

**Xác nhận T9.5 (camera thật trên iPhone, HTTPS công khai — điều kiện
FR7):** video hiện inline đúng, box + tip vẽ đúng vị trí, card kết quả
đúng — test bằng cách chĩa camera vào ảnh tư thế `downward` trên màn hình
laptop: detect đúng `downward` conf 92%, `form_ok=false`, tip "Đẩy hông
lên cao hơn để tạo hình chữ V ngược rõ hơn.", latency 4705ms (khớp tầm
Render free tier CPU-giới hạn đã ghi nhận).
