# Kịch bản quay video — dạng checklist (demo-focused)

Không phải văn bản đọc nguyên văn — mỗi bước là **hành động cụ thể** +
**ý nói ngắn gọn** (tự diễn đạt lại bằng lời bạn) + **thời lượng ước
lượng**. Tổng mục tiêu 5-10 phút (300-600s). Trọng tâm đặt vào phần demo
app chạy thật (mục 6) — các phần trước rút gọn tối đa.

Chuẩn bị trước khi bấm quay:
- [ ] Mở sẵn `https://computer-vision-project.pthieu290998.workers.dev`
      trước ~1 phút để "đánh thức" Render (free tier ngủ sau 15 phút
      không dùng — tránh video có đoạn chờ dài).
- [ ] Mở sẵn `docs/slides/presentation.html` (hoặc `.pptx`) ở tab/cửa sổ
      khác để chuyển qua lại lúc quay.
- [ ] Có điện thoại thật kết nối mạng, camera hoạt động, để quay đoạn
      demo camera trực tiếp (T9.5 đã xác nhận chạy đúng).

---

## 1. Mở đầu (~20s)

Slide 0 (cover). Nói tên dự án + 1 câu bài toán:
> "Yoga Pose Detection & Form Scoring — phát hiện tư thế yoga bằng
> YOLOv8, chấm điểm form bằng góc khớp, deploy public thật."

## 2. Bài toán + kiến trúc (~40s)

Slide 1-2. Ý cần nói:
- Input ảnh/video → output vị trí + tên tư thế + form đúng/sai + tip.
- 2 lớp: YOLOv8 **tự train** (detect+classify) vs MediaPipe **pretrained**
  vs rule-based **tự nghĩ** (chấm form) — không lẫn lộn 3 loại.

## 3. Dữ liệu + Training (~60s)

Slide 3-4. Ý cần nói:
- 5 lớp, Roboflow, 1013 ảnh. README ghi "không augmentation" nhưng 59/101 ảnh
  test là bản lật/crop của ảnh train → chia lại theo nhóm ảnh trùng.
- Đo lại: mAP@0.5:0.95 của model cũ từ 0.833 xuống 0.774 trên test sạch; train
  lại trên split sạch được 0.824.

## 4. Kết quả (~70s)

Slide 5-8. Ý cần nói (đọc thẳng số trên slide, không cần thuộc):
- Test sạch lộ ra lỗi thật: 7/154 ảnh, toàn bộ shoulderstand. OOD 45 ảnh: 82.2%,
  lỗi tập trung ở plank.
- Feedback loop: đổi sang yolov8s, đo trước/sau → **không cải thiện**, giữ yolov8n.
  Nói thẳng kết quả âm, kèm giả thuyết và hướng tiếp theo.
- Form scoring: 14/15 + 5/5, có 2 hạn chế đã biết (MediaPipe pose lộn ngược, góc
  2D bị méo khi camera chụp xiên).
- Stress test thẳng vào Render: 8 request đồng thời lúc đầu lỗi 25%, sửa lần 1 còn
  làm server sập, giới hạn 2 ảnh xử lý cùng lúc thì 0% lỗi.

## 5. Lỗi & bài học (~30s)

Slide 10. Kể bài học lớn nhất trước:
> "Mình đã tin README của dataset ghi không có augmentation, nên lúc đầu điểm gần
> như tuyệt đối và kết luận là không có gì để sửa. Kiểm tra lại thì hơn nửa tập test
> là bản sao ảnh train. Chia lại dữ liệu mới thấy lỗi thật. Hiệu năng cũng vậy: đo
> trên máy train thì ổn, bắn thẳng vào server thật mới thấy server sập khi nhiều
> người dùng cùng lúc."

## 6. Demo app chạy thật (~2.5-4 phút — phần trọng tâm)

**Đây là phần quan trọng nhất theo yêu cầu "chỉ cần video app chạy".**
Quay màn hình thật, thao tác thật, không dùng ảnh chụp sẵn.

- [ ] Mở `https://computer-vision-project.pthieu290998.workers.dev`
      (chỉ trỏ camera màn hình vào trình duyệt, hoặc quay màn hình máy
      tính/điện thoại trực tiếp).
- [ ] Tab **Upload ảnh** → chọn 1 ảnh yoga bất kỳ (có thể dùng ảnh trong
      `data/pose_rule_samples/`, hoặc ảnh mới hoàn toàn) → chờ kết quả →
      chỉ vào box + tên tư thế + % confidence + card "Form ổn"/"Cần
      chỉnh form" + tip. Nói 1 câu: "Đây là kết quả thật từ model, không
      dựng sẵn."
- [ ] Chuyển sang tab **Camera trực tiếp** trên điện thoại thật → bấm
      "Bật camera" → cho quyền → đứng vào khung hình làm 1 tư thế yoga
      bất kỳ → đợi vài giây (Render CPU free tier chậm, ~5-8s/lần, nói
      luôn lý do nếu video có đoạn chờ) → chỉ vào box/tip vẽ đúng vị trí
      trên người thật.
- [ ] (Tuỳ chọn nếu còn thời gian) Mở nhanh `GET /health` hoặc DevTools
      Network tab cho thấy request `/predict` thật, không phải giả lập.

## 7. Kết (~15s)

Slide 12. Cảm ơn + nhắc link repo/demo hiện trên màn hình.

---

**Tổng ước lượng:** ~5-7 phút (chưa tính khoảng chờ Render cold-start
nếu có) — nằm trong khoảng 5-10 phút yêu cầu; nếu ngắn hơn 5 phút, kéo dài
phần 6 (demo) bằng cách thử thêm 1-2 tư thế khác thay vì thêm lý thuyết.
