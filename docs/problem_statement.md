# Problem Statement

## Bài toán
Phát hiện và phân loại động tác (tư thế) yoga của học viên trong ảnh/video, sau đó
chấm điểm độ chính xác của form và đưa ra gợi ý cải thiện.

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
| v1 (an toàn deadline) | [YOLO YOGA Dataset – Roboflow Universe](https://universe.roboflow.com/object-detection-dt-wzpc6/yolo-yoga-dataset) | 5 (Bridge, Downward Dog, Plank, Shoulderstand, Tree) | Có sẵn bounding box, format YOLO, ~1013 ảnh |
| v2 (nếu có GPU server) | Yoga-82 (classification) + bootstrap bbox bằng pretrained person detector | 15–20 | Xem `src/data/bootstrap_bbox.py` |

So sánh v1 → v2 (thêm lớp, thêm dữ liệu) chính là câu chuyện cho mục 5 (Feedback
loop – cải tiến), có số liệu mAP trước/sau rõ ràng.
