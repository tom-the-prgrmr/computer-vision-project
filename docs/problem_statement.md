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
