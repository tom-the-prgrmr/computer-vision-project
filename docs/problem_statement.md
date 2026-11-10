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

> ⚠️ **Đã bị thay thế (Giai đoạn 12):** split gốc của Roboflow **rò rỉ** — 59/101 ảnh
> test và 122/203 ảnh valid là bản lật/crop của ảnh train, dù README của dataset ghi
> "No image augmentation". Từ Giai đoạn 12 dùng split chia lại theo nhóm ảnh trùng:
> train 703 / valid 156 / test 154 — xem mục "Rò rỉ dữ liệu & đánh giá lại (Giai đoạn 12)" cuối tài liệu.

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

> ⚠️ **Đã bị thay thế (Giai đoạn 12):** con số này đo trên test gốc bị rò rỉ nên bị thổi
> phồng. Cùng model, chỉ tính 42 ảnh test sạch: mAP@0.5:0.95 **0.774** (thay vì 0.833).
> Model train lại trên split sạch: mAP@0.5 **0.991**, mAP@0.5:0.95 **0.824** trên 154 ảnh
> test mới — xem mục "Rò rỉ dữ liệu & đánh giá lại (Giai đoạn 12)" cuối tài liệu.

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

> ⚠️ **Lưu ý (Giai đoạn 12):** cả hai run được đo trên test gốc bị rò rỉ. Ablation chưa
> chạy lại trên split sạch, nên chênh lệch ON/OFF ở đây chỉ để tham khảo.

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

> ⚠️ **Đã bị thay thế (Giai đoạn 12):** "không có lỗi" là do 58% tập test là bản sao
> ảnh train. Trên test sạch 154 ảnh, model train lại có **7 ảnh lỗi, toàn bộ là
> `shoulderstand`** (bị nhầm sang `bridge`/`downward` hoặc bỏ sót) — xem mục "Rò rỉ dữ liệu & đánh giá lại (Giai đoạn 12)" cuối tài liệu.

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

> ⚠️ **Đã bị thay thế (Giai đoạn 12):** tập OOD mở rộng lên 45 ảnh, đủ 5 lớp (thêm 27
> ảnh Wikimedia Commons). Model cũ đạt **40/45 (88.9%)**, lỗi tập trung ở `plank`. Vòng
> feedback loop được làm lại trên split sạch, có retrain thật và bảng trước/sau — xem
> mục "Rò rỉ dữ liệu & đánh giá lại (Giai đoạn 12)" cuối tài liệu.

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

> ⚠️ **Bổ sung (Giai đoạn 12):** số latency ở đây là 1 request đơn lẻ. Stress test bắn
> thẳng vào bản deploy trên Render (nhiều request đồng thời) nằm ở mục "Rò rỉ dữ liệu & đánh giá lại (Giai đoạn 12)" cuối tài liệu.

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

## Rò rỉ dữ liệu & đánh giá lại (Giai đoạn 12)

Chi tiết đầy đủ: `docs/specs/g12-sua-ro-ri-va-do-prod.md`. Mục này thay thế các kết
luận Giai đoạn 2-5 ở trên; các đoạn cũ được giữ lại làm lịch sử.

### Phát hiện

README của dataset Roboflow ghi "No image augmentation", nhưng nhiều ảnh valid/test là
bản **lật ngang** hoặc **crop/zoom** của ảnh train. `src/data/dedup_split.py` gom ảnh
trùng thành nhóm bằng 3 tín hiệu: cùng tên nguồn và cùng lớp; dHash 16×16 kể cả bản
lật; ORB + RANSAC cho bản crop/zoom. Các nhóm được nối bắc cầu bằng union-find. Ngưỡng
được hiệu chỉnh trên dữ liệu thật và kiểm tra tận mắt.

| Split gốc | Tổng | Trùng nhóm với ảnh train | Sạch |
|---|---|---|---|
| valid | 203 | 122 | 81 |
| test | 101 | **59** | **42** |

1013 ảnh chỉ có **552 nhóm ảnh độc lập**.

### Model cũ trên test sạch

| `yolov8n_v1_baseline`, test gốc | mAP@0.5 | mAP@0.5:0.95 | P | R |
|---|---|---|---|---|
| đủ 101 ảnh (có rò rỉ) | 0.994 | 0.833 | 0.987 | 0.977 |
| 42 ảnh sạch | 0.995 | **0.774** | 0.964 | 0.977 |

Rò rỉ thổi phồng mAP@0.5:0.95 khoảng **6 điểm**. mAP@0.5 gần như không đổi: ở IoU 0.5,
v1 vẫn thật sự dễ. Lỗi thật nằm ở độ khít của box và ở ảnh ngoài phân bố.

### Split mới và train lại

Chia lại theo nhóm, tỉ lệ 70/15/15, phân tầng theo lớp, seed 42: **train 703 / valid
156 / test 154 ảnh, không nhóm nào nằm ở hai split**. Danh sách chia được commit ở
`data/splits/yoga_v1_clean_manifest.csv` để Colab tái tạo đúng split.

`yolov8n_v1_clean_baseline` dùng cùng config chính thức (`yolov8n.pt`, seed 42, 50
epoch, augmentation ON). Trên test mới 154 ảnh: **mAP@0.5 0.991, mAP@0.5:0.95 0.824,
P 0.953, R 0.987**. Theo lớp (mAP@0.5:0.95): bridge 0.884, downward 0.881, plank 0.816,
shoulderstand 0.789, tree 0.751.

### Error analysis trên lỗi thật

- **Test sạch, conf 0.5: 7/154 ảnh có lỗi, toàn bộ là `shoulderstand`.** Gồm 4 bỏ
  sót, 3 nhầm lớp (2 → `bridge`, 1 → `downward`) và 2 box thừa. Theo từng ảnh, nguyên
  nhân là ảnh đồ hoạ/minh hoạ, nhiều người chồng lấn, hoặc người nhỏ ngược sáng.
- **EigenCAM trên ảnh sai:** ở ảnh nhiều người, vùng kích hoạt trải ra nền thay vì vào
  người; ở hình vẽ, nó chỉ phủ một dải hẹp quanh hông.
- **OOD mở rộng: 45 ảnh, đủ 5 lớp, 8-10 ảnh/lớp.** Gồm 18 ảnh Kaggle cũ và 27 ảnh
  Wikimedia Commons có license rõ ràng, đã kiểm tra không trùng với Roboflow.
  `clean_baseline` đúng **37/45 (82.2%)**; 6/8 ảnh sai là `plank` (side plank, cảnh
  ngoài trời có người nhỏ hoặc đông người).
- Lỗi trên test (shoulderstand) và lỗi OOD (plank) rơi vào hai lớp khác nhau. Nghĩa là
  test cùng phân bố không đại diện cho lỗi người dùng thật gặp.

### Feedback loop (rubric mục 5), làm lại

Thay đổi duy nhất: `yolov8n.pt` → `yolov8s.pt` (model lớn hơn), giữ nguyên seed, epoch
và dữ liệu.

| Run | mAP@0.5 | mAP@0.5:0.95 | Ảnh test lỗi | OOD |
|---|---|---|---|---|
| `yolov8n_v1_clean_baseline` (trước) | 0.991 | **0.824** | **7** | **82.2%** |
| `yolov8n_v1_clean_feedback`, yolov8s (sau) | 0.988 | 0.816 | 10 | 71.1% |

**Không cải thiện:** kém hơn ở cả 3 thước đo, dù mAP trên valid nhỉnh hơn 0.7 điểm.
Giả thuyết (chưa kiểm chứng): model có số tham số gấp ~3.5 lần nên khớp quá mức với 703
ảnh train. Giới hạn: chỉ 1 seed, và test chỉ có 88 nhóm độc lập, nên chênh dưới 1 điểm
mAP nằm trong nhiễu. Thay đổi này cũng không nhắm đúng pattern lỗi quan sát được
(người nhỏ, đông người, biến thể tư thế). Hướng tiếp theo hợp lý hơn là tăng
augmentation `scale` cho người nhỏ và bổ sung ảnh side plank, ảnh ngoài trời.

### Model chạy PROD

| Model (ONNX, đo qua đúng code của app, conf 0.5) | OOD đúng | Không phát hiện |
|---|---|---|
| `yolov8n_v1_baseline` (cũ, đang chạy PROD) | **40/45** | 4 |
| `yolov8n_v1_clean_baseline` | 37/45 | — |
| `yolov8n_v1_final_alldata` (train lại trên đủ 1013 ảnh) | 37/45 | 6 |

Không model mới nào hơn model đang chạy, nên **giữ nguyên model PROD**. Model cũ và
`final_alldata` cùng config, cùng dữ liệu mà vẫn chênh 3/45 ảnh: đây là mức dao động
giữa các lần train, không phải bằng chứng model cũ tốt hơn một cách có hệ thống. Số đo
**trung thực** của model PROD là trên 42 ảnh test sạch (mAP@0.5:0.95 0.774) và OOD
40/45. Không dùng số trên 101 ảnh test gốc.

### Hiệu năng trên PROD (Render free, 512 MB RAM)

`scripts/load_test.py` bắn request thẳng vào URL public, dùng cùng một ảnh 740×1159,
20 request ở mỗi mức đồng thời (kết quả trong `docs/perf/`):

| Đồng thời | Trước: lỗi / p95 / req/s | Threadpool: lỗi / p95 / req/s | Threadpool + giới hạn 2: lỗi / p95 / req/s |
|---|---|---|---|
| 1 | 0% / 6.3s / 0.19 | 5% / 6.6s / 0.18 (1 lỗi 502 chưa giải thích được) | 0% / 6.1s / 0.20 |
| 2 | 0% / 10.9s / 0.20 | 0% / 8.5s / 0.28 | 0% / 9.3s / 0.26 |
| 4 | 10% / 42.1s / 0.21 | 0% / 13.3s / 0.37 | 0% / 16.4s / 0.27 |
| 8 | 25% / 49.1s / 0.18 | **100% lỗi 502** | **0% / 31.1s / 0.27** |

- **Trước:** route `async def` chạy code nặng CPU trực tiếp nên chặn event loop. Mọi
  request phải xếp hàng nối tiếp: server mất ~4.8s/ảnh, thời gian chờ phía client tăng
  tuyến tính.
- **Threadpool:** ở 2-4 request đồng thời, throughput tăng 1.4-1.8 lần và p95 giảm từ
  42s xuống 13s. Nhưng ở 8 request đồng thời, process chết rồi khởi động lại: 8 request
  đầu lỗi cùng lúc, các request sau lỗi ngay. Giả thuyết là **hết RAM** (512 MB) — chưa
  xác nhận qua log Render, nhưng tái hiện được ở local: peak RSS 555 MB khi không giới
  hạn, 362 MB khi chỉ xử lý 2 ảnh cùng lúc (với ảnh điện thoại 12 MP: 1032 MB → 510 MB).
- **Threadpool + giới hạn 2 ảnh cùng lúc** (`MAX_CONCURRENT_PREDICTIONS=2`, đo
  2026-11-10): **80/80 request thành công ở mọi mức**, kể cả 8 đồng thời (trước đó 25% và
  100% lỗi). Đổi lại throughput dừng ở ~0.27 req/s thay vì 0.37 và p95 ở 4 đồng thời là
  16s thay vì 13s: request thứ 3 trở đi xếp hàng chờ thay vì làm sập server. Server p50
  giữ ~7s từ mức 2 trở lên, đúng như chỉ có 2 ảnh được xử lý cùng lúc — xác nhận bản có
  giới hạn đang chạy trên Render. Việc process không còn chết khi giới hạn RAM ủng hộ giả
  thuyết hết RAM, nhưng vẫn chưa phải bằng chứng trực tiếp từ log.
- **Cold start thật** (service ngủ nhiều ngày): `/health` trả lời sau **22.5s**, `/predict`
  đầu tiên thêm **10.1s** (nạp ONNX + MediaPipe lần đầu) → người dùng đầu tiên chờ ~33s.

### Bài học

Tin README của dataset mà không kiểm tra khiến mọi kết luận Giai đoạn 2-5 dựa trên số
liệu ảo, nhất là kết luận "không có lỗi để sửa" ở Giai đoạn 4-5. Kiểm tra trùng lặp
giữa các split nên là bước đầu tiên của khâu Data, trước khi train.
