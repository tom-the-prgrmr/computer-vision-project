# Spec — g8. Web demo local (rubric: mục 7 — Deployment, phần frontend)

**Plan source:** `docs/PLAN.md` — Giai đoạn 8
**Status:** implemented <!-- T8.1/T8.2 verify thật xong; T8.3 camera thật + T8.4 (nếu có bug) cần bạn tự làm, xem Implementation notes -->

## Bối cảnh quan trọng

`web/index.html` **đã được code đầy đủ từ trước** (tabs Upload/Camera,
`callPredict()`, `drawDetections()` vẽ box + tip lên canvas, xử lý lỗi
camera) — không phải stub `NotImplementedError`. Giai đoạn 8 vì vậy là
**verify** (xác nhận chạy đúng với backend thật, tìm bug nếu có) chứ
không phải viết mới từ đầu.

Môi trường này **có** công cụ Playwright (trình duyệt Chromium điều
khiển được — navigate, click, upload file, đọc console/network) — đủ để
tự động hoá thật T8.1/T8.2 và một phần T8.3, không hoàn toàn phải nhờ
bạn làm hết như các bước "cần Colab" trước đây.

**Giới hạn thật của Playwright ở đây:** không có camera thật, và không
rõ có kiểm soát được cờ `--use-fake-device-for-media-stream` của Chromium
hay không (server Playwright quản lý trình duyệt, không thấy tham số
này trong các tool có sẵn) — nên phần "camera thật chụp được khung hình
đúng, overlay đúng vị trí trên khung hình thật" **vẫn cần bạn tự làm trên
máy có webcam thật/điện thoại**, đây là external-blocked thật sự, không
né tránh.

## Việc cụ thể

**T8.1 — Chạy server thật (làm được ở đây):**
- Start `uvicorn app.main:app` (background, cổng 8000) với
  `MODEL_PATH=models/best.onnx` (đã có sẵn từ Giai đoạn 7) — xác nhận
  `GET /health` trả `{"status":"ok"}`.
- Serve `web/` bằng static server riêng (`python -m http.server 8080 --directory web`)
  thay vì mở trực tiếp `file://` — `fetch()` từ `file://` tới
  `http://localhost:8000` có thể bị Chromium chặn CORS do origin `file://`
  không nhất quán; serve qua HTTP giống thật hơn (CORS `allow_origins=["*"]`
  ở `app/main.py` đã cho phép).

**T8.2 — Test tab "Upload ảnh" bằng Playwright (làm được ở đây, test thật
với backend thật):**
- Navigate tới `http://localhost:8080/index.html`, click tab "Upload
  ảnh", `browser_file_upload` 1 ảnh thật (vd
  `data/pose_rule_samples/tree/...jpg`), đọc `#result` sau khi có response.
- Xác nhận: JSON hiển thị đúng có `detections`/`latency_ms`, `<img id="preview">`
  hiện ảnh đã chọn, không có lỗi console (`browser_console_messages`,
  level error), request `POST /predict` trả 200 (`browser_network_requests`).

**T8.3 — Test tab "Camera trực tiếp" (chia 2 phần, xem giới hạn ở trên):**
- *Phần làm được ở đây:* Playwright click "Bật camera", đọc console — kỳ
  vọng thấy lỗi `getUserMedia` grateful-fail (đúng nhánh code đã có:
  `camStatus.textContent = "Không mở được camera: ..."`, không crash JS)
  vì môi trường này không có camera thật. Đây CHỈ xác nhận nhánh lỗi
  không crash, không xác nhận luồng camera thật chạy đúng.
- *Phần cần bạn tự làm (ngoài môi trường này):* mở
  `http://localhost:8080` (hoặc `http://<ip-máy>:8080` từ điện thoại
  cùng mạng LAN — camera trên `localhost` không cần HTTPS theo PLAN.md),
  bấm "Bật camera", xác nhận thấy hình ảnh trực tiếp + box/tip vẽ đè
  đúng vị trí lên người trong khung hình (không lệch).

**T8.4 — Fix lệch toạ độ overlay (chỉ làm nếu tìm thấy bug thật):**
- Đã review tĩnh logic hiện tại (xem "Rủi ro" bên dưới) — có vẻ đúng,
  nhưng **chỉ xác nhận chắc chắn được sau khi bạn tự test T8.3 phần
  camera thật**. Nếu bạn thấy box/tip vẽ lệch vị trí thật, báo lại (kèm
  ảnh chụp màn hình nếu được) — mình sẽ sửa `resizeOverlay()`/`drawDetections()`
  trong `web/index.html` theo đúng lỗi quan sát được, không đoán trước.

## File/module liên quan

- `web/index.html` (đã có, chỉ sửa nếu T8.4 tìm ra bug thật)
- Không có file `src/`/`app/` nào cần đổi ở giai đoạn này (backend đã
  xong từ Giai đoạn 7)

## Bằng chứng / số liệu kỳ vọng

- T8.1/T8.2: log Playwright (screenshot + network request 200 + JSON kết
  quả thật hiển thị đúng trên trang)
- T8.3: bạn xác nhận bằng mắt trên máy có webcam thật — không có gì để
  mình tự sinh ra "bằng chứng" ở đây ngoài lời xác nhận của bạn

## Cách bạn tự test sau khi tôi xong

1. Server đã chạy sẵn ở `http://localhost:8000` (mình start), trang web ở
   `http://localhost:8080` (mình cũng start) — hoặc bạn tự chạy lại:
   ```bash
   uvicorn app.main:app --reload
   python -m http.server 8080 --directory web
   ```
2. Mở `http://localhost:8080` trên trình duyệt máy bạn (có webcam thật).
3. Tab "Camera trực tiếp" → bấm "Bật camera" → cho phép quyền camera →
   đứng vào khung hình làm 1 tư thế yoga bất kỳ trong 5 lớp → xem box +
   tên tư thế + tip (nếu có) có vẽ đúng vị trí lên người trong hình
   không (không bị lệch/trôi).
4. Báo lại: đúng vị trí hay lệch (kèm ảnh chụp màn hình nếu lệch, để
   mình sửa đúng chỗ).

## ❓ Quyết định cần bạn chốt

Không có.

## Rủi ro / điều cần lưu ý

- **Review tĩnh logic toạ độ overlay** (trước khi test thật): `captureAndPredict()`
  tạo canvas chụp khung hình với `canvas.width = camVideo.videoWidth`
  (độ phân giải gốc camera, không phải kích thước hiển thị CSS) rồi gửi
  lên API — box trả về nằm trong hệ toạ độ pixel gốc này.
  `resizeOverlay()` set `camOverlay.width/height` **cũng** bằng
  `camVideo.videoWidth/videoHeight` — cùng hệ toạ độ với box trả về.
  Canvas overlay CSS `inset:0; width:100%; height:100%` bên trong
  `#camWrap` — mà `#camWrap` không set height cứng, chiều cao của nó do
  chính `<video>` (phần tử duy nhất trong luồng layout — canvas
  `position:absolute` không tính vào) quyết định, và `<video>` giữ đúng
  tỉ lệ khung hình gốc khi chỉ set `width:100%`. Nên canvas và video
  cùng khung CSS, cùng tỉ lệ khung hình → trình duyệt tự scale nội dung
  canvas khớp đúng vị trí hiển thị. **Về lý thuyết không thấy bug** —
  nhưng đây là loại lỗi (T8.4 đặt tên "lỗi thường gặp") chỉ hiện rõ khi
  chạy thật trên thiết bị thật, review tĩnh không thay được test thật.
- `CAPTURE_INTERVAL_MS = 400` (~2.5 fps) — nếu máy/mạng bạn chậm hơn,
  `inFlight` guard đã có sẵn tránh dồn request, không cần sửa.
- Camera trên điện thoại thật qua HTTPS công khai là Giai đoạn 9, không
  phải giai đoạn này (giai đoạn này chỉ cần `localhost`/LAN theo PLAN.md).

## Implementation notes

**Không sửa `web/index.html`** — code đã đúng từ trước, verify không tìm
ra bug nào cần sửa (T8.4 không áp dụng, xem bên dưới).

**T8.1 — làm thật, kết quả thật:** `uvicorn app.main:app` (port 8000,
`MODEL_PATH=models/best.onnx` mặc định) chạy nền, `GET /health` trả
`{"status":"ok"}`. `python -m http.server 8080 --directory web` serve
trang web. Cả 2 server vẫn đang chạy — bạn có thể mở
`http://localhost:8080` ngay bằng trình duyệt thật trên máy để test
tiếp, không cần khởi động lại.

**T8.2 — làm thật bằng Playwright, kết quả thật:** navigate
`http://localhost:8080`, click tab Upload, upload 1 ảnh thật
(`data/pose_rule_samples/tree/...jpg`) → response
`{"pose":"tree","confidence":0.92,"form_ok":true,...}` — khớp đúng kết
quả `curl` thật đã có ở Giai đoạn 7. `POST /predict` trả 200
(`browser_network_requests`), preview ảnh hiện đúng, không có lỗi
console (chỉ có 1 warning 404 `favicon.ico`, vô hại, không phải bug).

**T8.3 — chia 2 phần đúng như spec dự kiến:**
- *Đã làm ở đây (Playwright):* click "Bật camera" — không có webcam thật
  trong môi trường này nên `getUserMedia()` fail đúng như dự kiến
  (`"Requested device not found"`), nhưng xử lý lỗi đúng: không crash JS,
  `camStatus` hiện thông báo rõ ràng, nút bấm trở về đúng trạng thái ban
  đầu (start enabled, stop/flip disabled) — không kẹt UI. Xác nhận nhánh
  lỗi hoạt động đúng.
- *Cần bạn tự làm (webcam thật):* mở `http://localhost:8080` bằng trình
  duyệt thật, bấm "Bật camera", xác nhận box/tip vẽ đúng vị trí lên
  người trong khung hình (không lệch) — xem "Cách bạn tự test".

**T8.4:** không tìm ra bug qua review tĩnh + phần test Playwright test
được — để trống, chỉ sửa nếu bạn báo có lệch thật khi tự test T8.3.

**Cải tiến thêm theo yêu cầu (ngoài PLAN.md, hợp lý nên làm cùng lúc):**
1. Tab Upload trước đây chỉ hiện `<img>` gốc + JSON text — giờ vẽ box +
   tip đè lên chính ảnh (giống tab Camera), dùng `<canvas>` thay `<img>`.
   Tách logic vẽ (`drawDetectionsOnto()`) dùng chung cho cả 2 tab, tránh
   lặp code (trước đó gắn cứng trong closure của tab Camera).
2. Khu vực kết quả trước đây chỉ dump JSON thô — giờ hiện card đọc được
   (tên tư thế + %, trạng thái "✓ Form ổn"/"✗ Cần chỉnh form" màu xanh/đỏ,
   tip dạng bullet), dùng chung cho cả Upload lẫn Camera. JSON gốc vẫn giữ
   trong `<details>` gấp lại để debug khi cần, không bỏ hẳn.

Verify bằng Playwright (2 vòng): (a) ảnh `plank` form đúng → box xanh +
card "✓ Form ổn"; (b) ảnh `plank` form sai (case oblique-angle đã biết từ
Giai đoạn 6) → box đỏ + card "✗ Cần chỉnh form" kèm đúng tip. Cả 2 không
lỗi console.

**Xác nhận thêm từ bạn (trình duyệt thật, ảnh ngoài mọi dataset đã dùng —
ảnh biển, ánh sáng ngược):** đúng `downward`, confidence 0.954,
`form_ok=false` kèm tip "Đẩy hông lên cao hơn để tạo hình chữ V ngược rõ
hơn." — hợp lý khi nhìn ảnh (hông chưa đẩy lên rõ rệt). Xác nhận cả 2 lớp
(detector + rule-based form scoring) chạy đúng cùng nhau trên ảnh thật
hoàn toàn mới, qua đúng trình duyệt thật của người dùng — bằng chứng mạnh
hơn test Playwright ở trên.
