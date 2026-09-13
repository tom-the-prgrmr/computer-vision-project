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

## 3. Dữ liệu + Training (~40s)

Slide 3-4. Ý cần nói:
- 5 lớp, Roboflow, v2 (15-20 lớp) chỉ dừng ở thiết kế vì v1 đã đủ tốt.
- seed=42, epochs=50, ablation augmentation ON thắng OFF.

## 4. Kết quả (~50s)

Slide 5-8. Ý cần nói (đọc thẳng số trên slide, không cần thuộc):
- Confusion matrix sạch, EigenCAM nhìn đúng chỗ.
- OOD 94.4% (17/18) → không cần retrain.
- Form scoring: 14/15 + 5/5, có 2 hạn chế đã biết (MediaPipe pose lộn
  ngược, góc 2D bị méo khi camera chụp xiên).
- Latency: ONNX nhanh hơn PyTorch ~17%, CPU free tier chậm hơn (không
  phải bug).

## 5. Lỗi & bài học (~30s)

Slide 10. Chọn 1-2 bug kể cho sinh động, vd:
> "Lúc đầu OOD accuracy báo 0% — hoá ra do chưa bỏ tiền tố tên lớp, sửa
> xong ra 94.4%. Lúc deploy cũng dính đủ thứ: chọn nhầm runtime nên
> thiếu thư viện, rồi camera iPhone bị đẩy vào chế độ xem toàn màn hình
> của iOS — đều tự chẩn đoán qua log/screenshot thật, không đoán mò."

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

**Tổng ước lượng:** ~4.5-6.5 phút (chưa tính khoảng chờ Render cold-start
nếu có) — nằm trong khoảng 5-10 phút yêu cầu; nếu ngắn hơn 5 phút, kéo dài
phần 6 (demo) bằng cách thử thêm 1-2 tư thế khác thay vì thêm lý thuyết.
