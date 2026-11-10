<!--
Slide tóm tắt dự án — dùng làm dàn ý quay video Giai đoạn 11 (T11.1-T11.3).
Format: mỗi `---` là 1 slide (tương thích Marp/reveal.js nếu cần convert
sau: `marp docs/slides/summary.md --pdf`). Số liệu lấy từ
docs/problem_statement.md, không đo lại ở đây.

Bản trình chiếu thật, cùng nội dung, 2 định dạng:
- docs/slides/presentation.html — mở trực tiếp trong trình duyệt, điều
  hướng bằng phím mũi tên.
- docs/slides/presentation.pptx — PowerPoint chuẩn, mở bằng
  PowerPoint/Google Slides/LibreOffice Impress, chỉnh sửa tay được (sinh
  từ scripts/build_pptx.py qua python-pptx).
File này (.md) là dàn ý/nội dung gốc.
-->

# Yoga Pose Detection & Form Scoring

Mini Project — Computer Vision Module (AI Engineer K08-0226)

Phát hiện + phân loại tư thế yoga qua ảnh/video, chấm điểm form, deploy
thành web demo public.

---

## 1. Bài toán

- Input: ảnh/video học viên tập yoga.
- Output: vị trí + tên tư thế (5 lớp: bridge, downward, plank,
  shoulderstand, tree) + đánh giá form đúng/sai + gợi ý sửa.
- Ràng buộc đề bài: phải có 1 model classification/detection/segmentation
  **tự train** — chọn **YOLOv8 detection** (vừa localize vừa classify
  trong 1 bước, hỗ trợ nhiều học viên/khung hình).

---

## 2. Kiến trúc — 2 lớp độc lập

1. **YOLOv8 (tự train, ONNX-exported)** — detect + classify tư thế.
2. **MediaPipe Pose (pretrained) + rule-based angle scoring (tự nghĩ)** —
   crop box → 33 keypoint → so góc khớp với ngưỡng chuẩn từng tư thế →
   tip sửa form.

Sơ đồ đầy đủ: `docs/architecture.md`.

---

## 3. Dữ liệu — và rò rỉ dữ liệu (Giai đoạn 1 + 12)

- **v1**: 5 lớp, YOLO-format có sẵn bbox, Roboflow ("YOLO YOGA Dataset"), 1013 ảnh.
- **Rò rỉ:** README của dataset ghi "No image augmentation", nhưng **59/101 ảnh test**
  và 122/203 ảnh valid là bản lật ngang hoặc crop/zoom của ảnh train. Phát hiện bằng
  dHash (kể cả bản lật) + ORB/RANSAC, gom nhóm bằng union-find → chỉ **552 nhóm ảnh
  độc lập**.
- **Chia lại theo nhóm:** 703 / 156 / 154 ảnh, không nhóm nào nằm ở hai split;
  manifest commit vào repo để tái tạo.
- Augmentation: `fliplr` bật, `flipud` tắt, `degrees` giới hạn.

---

## 4. Training — đo lại trên test sạch

- YOLOv8n, seed 42, 50 epoch, imgsz 640, augmentation ON.

| Model · tập test | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|
| Model cũ · 101 ảnh test gốc (rò rỉ) | 0.994 | 0.833 |
| Model cũ · 42 ảnh test sạch | 0.995 | 0.774 |
| Train lại trên split sạch · 154 ảnh test mới | 0.991 | **0.824** |

- Rò rỉ thổi phồng mAP@0.5:0.95 khoảng 6 điểm; mAP@0.5 gần như không đổi.
- Ablation augmentation ON/OFF (chọn ON) đo trên test bị rò rỉ — chỉ để tham khảo.

---

## 5. Error analysis — test sạch lộ ra lỗi thật

- **7/154 ảnh test lỗi, toàn bộ là `shoulderstand`** (bỏ sót, nhầm sang
  bridge/downward): ảnh đồ hoạ, nhiều người chồng lấn, người nhỏ ngược sáng.
- EigenCAM trên ảnh **sai**: ảnh nhiều người, kích hoạt trải ra nền thay vì vào người.
- **OOD 45 ảnh, đủ 5 lớp** (Kaggle + Wikimedia Commons, không trùng Roboflow):
  **82.2%**, lỗi tập trung ở `plank` (side plank, ảnh ngoài trời đông người).
- Lỗi test và lỗi OOD rơi vào hai lớp khác nhau → test cùng phân bố không đại diện cho
  người dùng thật.

---

## 6. Feedback loop — một thay đổi, bảng trước/sau

| Run (cùng seed, cùng dữ liệu) | mAP@0.5:0.95 | Ảnh test lỗi | OOD |
|---|---|---|---|
| yolov8n · trước | **0.824** | **7** | **82.2%** |
| yolov8s · sau | 0.816 | 10 | 71.1% |

- **Không cải thiện** → giữ yolov8n. Giả thuyết: model gấp ~3.5 lần tham số khớp quá
  mức với 703 ảnh train (1 seed, chưa kiểm chứng).
- Thay đổi không nhắm đúng pattern lỗi quan sát được → hướng tiếp: augmentation `scale`
  cho người nhỏ, thêm ảnh side plank.
- PROD giữ model cũ (OOD 40/45): không model train lại nào hơn.

---

## 7. Form scoring (ý tưởng riêng — rubric mục 6)

- MediaPipe Pose (pretrained) → 33 keypoint → góc khớp → so `POSE_RULES`
  (hiệu chỉnh bằng số đo thật trên 15 ảnh mẫu, ±15°).
- Kết quả: 14/15 ảnh mẫu đúng form + 5/5 case tổng hợp lệch góc phát hiện
  đúng.
- **2 hạn chế thật, ghi nhận công khai:** MediaPipe kém tin cậy trên tư
  thế lộn ngược (nền tương phản thấp); góc chiếu 2D bị méo khi camera
  chụp xiên (hạn chế cố hữu, không phải bug).

---

## 8. Export, Backend & hiệu năng trên PROD

- Export ONNX: nhanh hơn PyTorch ~17% (GPU T4 Colab). `app/service.py`: load model 1
  lần, pipeline detect → crop → MediaPipe → `score_pose()` → JSON.
- **Stress test bắn thẳng vào Render** (`scripts/load_test.py`, `docs/perf/`):

| Request đồng thời | Trước: lỗi · p95 | Threadpool: lỗi · p95 | + giới hạn 2: lỗi · p95 |
|---|---|---|---|
| 1 | 0% · 6.3 s | 5% · 6.6 s (1 lỗi 502 chưa rõ) | 0% · 6.1 s |
| 2 | 0% · 10.9 s | 0% · 8.5 s | 0% · 9.3 s |
| 4 | 10% · 42.1 s | 0% · 13.3 s | 0% · 16.4 s |
| 8 | 25% · 49.1 s | 100% lỗi 502 | **0% · 31.1 s** |

- Trước: route `async def` chạy code nặng CPU, chặn event loop. Threadpool: nhanh hơn ở
  2-4 đồng thời, nhưng ở 8 đồng thời process chết — nghi hết RAM 512 MB (tái hiện ở
  local: peak 555 → 362 MB). Giới hạn 2 ảnh xử lý cùng lúc: **80/80 thành công**, đổi
  lại request xếp hàng lâu hơn.
- Cold start thật: ~33s cho người dùng đầu tiên (22.5s đánh thức + 10.1s nạp model).

---

## 9. Web demo & Deploy public

- `web/index.html`: tab Upload ảnh + Camera trực tiếp, vẽ box/tip đè lên
  ảnh, card kết quả đọc được (không chỉ dump JSON thô).
- Deploy: **Render** (backend, free) + **Cloudflare Pages** (frontend,
  free) — 2 origin khác nhau, CORS siết đúng domain.
- Demo live: https://computer-vision-project.pthieu290998.workers.dev

---

## 10. Lỗi & bài học

- **Bài học lớn nhất — dữ liệu:** tin README của dataset mà không kiểm tra → 58% ảnh
  test là bản sao ảnh train, mọi kết luận Giai đoạn 2-5 dựa trên số ảo. Kiểm tra trùng
  lặp giữa các split phải là bước đầu tiên của khâu Data.
- **Hiệu năng:** đo trên máy train không thấy lỗi thật; chỉ khi bắn thẳng vào Render mới
  lộ event loop bị chặn và process chết khi nhiều request.
- `mediapipe>=1.0` bỏ hẳn API cũ (`solutions.pose`) — pin đúng `==0.10.21`.
- Deploy: 3 bug môi trường thật (runtime Python thay vì Docker; thiếu `libGL.so.1`;
  iOS Safari đẩy camera vào native fullscreen) — chẩn đoán từ log/screenshot thật.

---

## 11. Demo

*(Quay video thật lúc trình bày — camera trực tiếp trên iPhone qua URL
public, upload ảnh, xem card kết quả + tip.)*

---

## Liên kết

- Repo: (điền link GitHub public)
- Demo live: https://computer-vision-project.pthieu290998.workers.dev
- Kiến trúc: `docs/architecture.md`
- Chi tiết đầy đủ 7 mục rubric: `docs/problem_statement.md`
