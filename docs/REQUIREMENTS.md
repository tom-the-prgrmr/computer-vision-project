# Requirements — Yoga Pose Detection & Form Scoring

Nguồn chân lý duy nhất cho scope dự án. Các file khác chỉ trích/tham chiếu file
này, không định nghĩa lại yêu cầu ở nơi khác.

- Đề bài gốc: `docs/reference/`
- Bài viết mục 1 (Problem statement) khi nộp bài: `docs/problem_statement.md`
- Theo dõi tiến độ theo rubric: `docs/requirement_checklist.md`

## 1. Tổng quan

Train 1 model Computer Vision phát hiện + phân loại động tác yoga của học viên
trên video, sau đó chấm đúng/sai form và gợi ý cải thiện. Đây là mini project
cuối module Computer Vision, cần đi đủ vòng đời: bài toán → dữ liệu → train →
đánh giá/phân tích lỗi → cải tiến → deploy.

## 2. Business requirement

- **Ai dùng**: người tự tập yoga tại nhà không có HLV kiểm tra trực tiếp; hoặc
  HLV muốn giám sát nhiều học viên cùng lúc qua camera lớp học.
- **Giá trị**: phát hiện học viên đang tập tư thế nào, biết form đúng/sai, và
  biết cần sửa gì — không cần người khác đứng cạnh chỉnh.
- **Đo thành công**: model detect/phân loại đúng tư thế với mAP đủ tin cậy
  trên tập test; lớp chấm điểm form đưa ra nhận định hợp lý khi đối chiếu thủ
  công (không có ground-truth chuẩn hoá cho phần này, xem mục 6).

## 3. Functional requirements

| ID | Yêu cầu | Đáp ứng bằng |
|---|---|---|
| FR1 | Nhận diện học viên đang tập yoga **trên video** (không chỉ ảnh tĩnh) | YOLOv8 infer theo từng frame, `model.track()` giữ ID ổn định |
| FR2 | Detect vùng nào là người tập | Bounding box output của YOLOv8 |
| FR3 | Phân loại động tác (tư thế) | Class output của YOLOv8 — cùng 1 forward pass với FR2 |
| FR4 | Gán nhãn đúng/sai form | Rule-based: MediaPipe Pose (pretrained) trích khớp trong box đã detect → so góc với ngưỡng chuẩn từng tư thế |
| FR5 | Đưa ra phương án cải thiện | Cùng lớp FR4, sinh tip theo khớp nào lệch ngưỡng (vd "duỗi thẳng chân trụ hơn") |
| FR6 | Serve qua API + web demo test được bằng ảnh hoặc video | FastAPI (`/predict` ảnh, `/predict_video` video file) + `web/index.html` |
| FR7 | Demo dùng được **camera trực tiếp trên điện thoại/iPhone**, không chỉ upload file | Web demo mở camera qua `getUserMedia` trong trình duyệt, chụp frame định kỳ, gọi `/predict` theo vòng lặp (client-side) — xem mục 5.1 |

**Chỉ 1 model được train** (YOLOv8 detection) đáp ứng FR1–FR3 trong 1 lần
infer/frame. FR4–FR5 là logic rule-based nối tiếp, không phải model thứ 2 cần
train — giữ đúng ràng buộc đề bài "1 trong 3 dạng bài toán đã học".

## 4. Non-functional requirements

- **Reproducibility**: mọi kết quả train/ablation phải chạy lại được với seed
  cố định (yêu cầu rõ trong đề bài mục 3).
- **Khả năng chạy lại từ đầu**: README phải đủ để người khác setup → train →
  serve mà không cần hỏi thêm.
- **Latency/FPS**: đo được tốc độ inference trước/sau export ONNX (và trước/
  sau quantization nếu có GPU thuê) — không cần đạt real-time tuyệt đối, chỉ
  cần có số liệu so sánh thật.
- **Không cần SOTA**: đề bài nói rõ trọng tâm là hiểu đúng vòng đời, không
  phải điểm số cao nhất.

## 5. Kiến trúc & phạm vi kỹ thuật

Chi tiết đầy đủ: `docs/problem_statement.md`. Tóm tắt:

```
Video học viên → YOLOv8 (fine-tuned, model train chính)
                     │ box + pose class
                     ▼
              MediaPipe Pose (pretrained)
                     │ 33 keypoints trong box
                     ▼
              Rule-based angle scoring
                     │ đúng/sai + tip
                     ▼
              FastAPI → Web demo
```

### 5.1 Hai kiểu "video" — đừng nhầm

- **Camera trực tiếp (chính, FR7)**: trình duyệt trên điện thoại mở camera
  bằng `getUserMedia`, JS chụp 1 frame mỗi ~300–500ms lên `<canvas>`, gửi ảnh
  đó tới `/predict` (endpoint ảnh đơn, đã có) theo vòng lặp, vẽ box/nhãn/tip
  đè lên `<video>`. Xử lý "video" nằm ở **vòng lặp phía client**, backend chỉ
  cần xử lý ảnh đơn — không cần `/predict_video` cho use case này.
- **Upload file video** (`/predict_video`, phụ): dùng khi muốn phân tích 1
  đoạn video đã quay sẵn (offline), không phải luồng chính của demo.

## 6. Phạm vi dữ liệu

| Giai đoạn | Nguồn | Số lớp | Trạng thái |
|---|---|---|---|
| v1 | Roboflow "YOLO YOGA Dataset" (có sẵn bbox, format YOLO) | 5 | Bắt buộc, làm trước — an toàn deadline |
| v2 | Kaggle Yoga-82 (classification) + bootstrap bbox qua pretrained person detector | 15–20 | Tuỳ chọn, chỉ làm nếu còn thời gian/có GPU thuê — kết quả v1→v2 dùng làm bằng chứng cho mục 5 (Feedback loop) |

v2 là **pseudo-label**, không phải ground-truth do người gán — phải nói rõ
điều này trong tài liệu nộp, không trình bày như dữ liệu đã kiểm định.

## 7. Ràng buộc & rủi ro đã biết

- **Deadline**: 15/9 (đề bài đăng 15/8). Ưu tiên có pipeline v1 chạy end-to-end
  (ảnh + video) sớm, mọi mở rộng (v2, GPU thuê, tối ưu) chỉ làm sau khi v1 ổn.
- **Compute**: mặc định Google Colab free (T4) — giới hạn giờ/session, ảnh
  hưởng số lượng ablation/epoch có thể chạy. Nếu thuê được GPU, xem phần "cải
  tiến khi có GPU" đã thảo luận trong lịch sử — không phải yêu cầu bắt buộc.
- **Grad-CAM cho detection**: thư viện `grad-cam` chuẩn thiết kế cho
  classifier (cần class score + gradient rõ ràng), không áp dụng thẳng được
  cho YOLO (nhiều box/lớp cùng lúc). Dùng **EigenCAM/EigenGradCAM** (không
  cần backprop qua class cụ thể, có hỗ trợ YOLOv8 trong `pytorch-grad-cam`)
  thay cho Grad-CAM cổ điển ở mục 4.
- **POSE_RULES (ngưỡng góc chuẩn)** trong `angle_rules.py` hiện là placeholder
  — cần hiệu chỉnh bằng ảnh/video mẫu form đúng trước khi tin kết quả chấm
  điểm.
- **HTTPS bắt buộc cho camera trên iPhone**: Safari (và Chrome Android) chặn
  `getUserMedia` trên origin không an toàn — chỉ chạy được trên `https://`
  hoặc `localhost`. Deploy demo lên IP/domain HTTP thường sẽ **không mở được
  camera trên điện thoại** dù vẫn mở được trên máy dev qua localhost. Cần TLS
  thật (Let's Encrypt/Caddy, hoặc PaaS có sẵn HTTPS) trước khi test trên
  iPhone — chưa chốt host cụ thể, để quyết định ở giai đoạn deploy.
- **CORS**: `app/main.py` hiện để `allow_origins=["*"]` cho tiện dev — phải
  siết lại về đúng domain frontend khi deploy thật.
- **Băng thông di động**: mỗi frame gửi lên nên nén JPEG chất lượng vừa phải
  (không gửi PNG/raw) để vòng lặp camera không bị nghẽn trên mạng 4G/wifi yếu.

## 8. Ngoài phạm vi (out of scope)

Ghi rõ để tránh scope creep giữa chừng:

- Không tự train model pose-estimation (dùng MediaPipe pretrained, không phải
  của mình).
- Không cần real-time streaming đa camera hay mobile app — web demo đơn giản
  (upload ảnh/video) là đủ theo đề bài.
- Không cần multi-object tracking phức tạp — `model.track()` mặc định của
  Ultralytics là đủ, không tự viết tracker riêng.
- Không cần đạt SOTA hay so sánh với paper — đề bài yêu cầu rõ điều này.
- v2 (mở rộng 15-20 lớp) là **stretch goal**, không phải điều kiện để coi dự
  án hoàn thành — v1 (5 lớp) chạy đủ vòng đời là đã đáp ứng đề bài.
- **Không cần database** — pipeline stateless (ảnh/frame vào → kết quả ra
  ngay), không lưu lịch sử/tài khoản người dùng. Nếu sau này muốn thêm "lịch
  sử tập luyện" như phần sáng tạo (mục 6), dùng SQLite (file, zero-ops) chứ
  không cần Postgres/MySQL — nhưng đây vẫn là optional, không bắt buộc.

## 9. Definition of Done theo giai đoạn

1. **Pipeline tối thiểu (bắt buộc)**: v1 data → train → eval (mAP, confusion
   matrix, EigenCAM, error cases) → export ONNX → FastAPI `/predict` (ảnh) →
   web demo ảnh chạy được.
2. **Video (bắt buộc theo FR1)**: `/predict_video` chạy được, form scoring áp
   dụng trên từng frame, web demo nhận video.
3. **Feedback loop (bắt buộc mục 5)**: ít nhất 1 hướng cải tiến có số liệu
   trước/sau — có thể là v1→v2 data, hoặc augmentation/imbalance handling nếu
   không kịp làm v2.
4. **Sản phẩm nộp**: README hoàn chỉnh, sơ đồ, tài liệu 7 mục, slide, video
   trình bày, repo public — theo `docs/requirement_checklist.md`.
