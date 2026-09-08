# Pose rule samples (Giai đoạn 6)

Ảnh "form đúng" dùng để hiệu chỉnh ngưỡng góc trong
`src/pose_scoring/angle_rules.py::POSE_RULES` — xem
`docs/specs/g6-form-scoring.md` (T6.1/T6.2).

**Nguồn:** chính dataset v1 của dự án —
[YOLO YOGA Dataset](https://universe.roboflow.com/object-detection-dt-wzpc6/yolo-yoga-dataset)
trên Roboflow (CC BY 4.0), gộp cả 3 split (test/valid/train). 3 ảnh/lớp ×
5 lớp = 15 ảnh, chọn tự động từ ảnh chỉ có đúng 1 bbox (1 người/ảnh, tránh
MediaPipe Pose bắt nhầm người phụ trong khung), **dedup theo tên file gốc
Roboflow** (bỏ hậu tố `.rf.<hash>`) để đảm bảo 3 ảnh/lớp là 3 nguồn ảnh
thật sự khác nhau — Roboflow xuất nhiều bản từ cùng 1 ảnh gốc (khác hash
hậu tố, cùng tên gốc), lần chọn đầu tiên vô tình lấy trùng nguồn cho
`tree` và `shoulderstand` (phát hiện qua `code-review`), đã chọn lại.

Đã xem mẫu bằng mắt toàn bộ 15 ảnh — đúng tư thế, ảnh rõ, người thật.

**2 hạn chế phát hiện được khi hiệu chỉnh (T6.2), 2 nguyên nhân khác nhau:**

- **`shoulderstand`/`File112`** (đã thay, không dùng nữa): nền cát/trời
  tương phản thấp khiến MediaPipe Pose detect landmark rất lệch (hip=96.8°,
  knee=62.4°, trong khi 2 ảnh cùng lớp đo ~155-160°/167-173°) dù ảnh nhìn
  bằng mắt vẫn đúng tư thế. Thay bằng `File116` (nền rõ hơn), kết quả nhất
  quán. Hạn chế: MediaPipe Pose kém tin cậy trên tư thế lộn ngược (đầu ở
  dưới) khi nền/tương phản không thuận lợi.
- **`plank`/`00000006`** (giữ nguyên, không thay): chụp góc chéo 3/4 (2
  ảnh plank còn lại chụp thẳng cạnh), đo hip=119.8° (trái/phải đồng nhất
  ~118-122 — không phải nhiễu detect ngẫu nhiên) trong khi 2 ảnh kia
  ~174-179°. Nguyên nhân khác: góc quay nghiêng làm méo góc chiếu 2D dù
  thân người thực tế thẳng — hạn chế cố hữu của việc tính góc từ 1 ảnh đơn
  (không có depth/3D), không phải lỗi detect landmark. Giữ ảnh này lại làm
  ví dụ minh hoạ hạn chế — `score_pose()` sẽ báo ảnh này "chưa thẳng thân",
  biết trước và chấp nhận được (xem comment tại `POSE_RULES["plank"]`
  trong `angle_rules.py`).

Dùng cho mục đích hiệu chỉnh ngưỡng, không phải benchmark có ground-truth
góc chuẩn — chỉ cần ảnh rõ đúng tư thế, không cần độ chính xác tuyệt đối.
