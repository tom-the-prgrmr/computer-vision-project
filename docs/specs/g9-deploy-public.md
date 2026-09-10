# Spec — g9. Deploy public (rubric: mục 7 — Deployment)

**Plan source:** `docs/PLAN.md` — Giai đoạn 9
**Status:** implemented <!-- Code xong cho phương án chính (Render + Cloudflare Pages) và phương án thay thế (VPS + Caddy); phần deploy thật + T9.5 (iPhone thật) cần bạn tự làm, xem Implementation notes -->

## Lịch sử đổi host (đọc trước, để hiểu vì sao có 2 bộ file deploy)

Giai đoạn này đổi host 2 lần dựa trên thông tin thật phát sinh khi bạn thao
tác thật (không phải đoán trước):

1. **HF Spaces (dự định ban đầu) → phát hiện Docker Space giờ bắt trả
   phí** khi bạn vào form tạo Space thật (ảnh chụp màn hình thật) — free
   chỉ còn Static Space, không chạy được backend Python.
2. **Chuyển sang VPS riêng của bạn** (có domain `hldhn.com`) — xây xong
   `Dockerfile` + `docker-compose.yml` + `Caddyfile` (Caddy tự xin HTTPS
   qua Let's Encrypt), review 2 vòng sạch. Sau đó bạn hỏi có chỗ free
   không (đỡ tốn VPS) → so sánh Oracle Cloud Free (cần thẻ Visa xác minh)
   vs Render free (không cần thẻ, có cold start) → bạn chọn **tách hẳn
   FE/BE**: **Render** (backend, Docker, free) + **Cloudflare Pages**
   (frontend tĩnh, free) — đây là **phương án chính hiện tại**.

Bộ file VPS + Caddy (`docker-compose.yml`, `Caddyfile`) **vẫn giữ lại
trong repo** làm phương án thay thế đã build + review xong sẵn, phòng khi
cần dùng VPS sau này (vd nếu Render free không đủ ổn định lúc quay demo) —
xem mục "Phương án thay thế: VPS + Caddy" bên dưới. Không phải file thừa.

## Bối cảnh quan trọng

Việc thật ở giai đoạn này chia làm 2 phần rõ rệt:

1. **Code hoá deploy-ready** (làm được ở môi trường này): sửa `web/index.html`
   để hỗ trợ chạy tách origin (FE Cloudflare Pages, BE Render), giữ CORS
   linh hoạt qua env, chuẩn bị `Dockerfile` cho Render build.
2. **Tạo tài khoản + connect repo + deploy thật** trên Render và Cloudflare
   Pages (external — cần tài khoản của bạn, môi trường này không có): mình
   đưa đúng các bước, bạn tự làm trên dashboard của 2 dịch vụ.

`models/best.onnx` (12MB) hiện bị `.gitignore` chặn ở repo GitHub chính
qua 2 rule chung (`models/*` và `*.onnx`, để loại checkpoint `.pt`/`.onnx`
thử nghiệm khác không đáng commit). Render build từ chính GitHub repo này
qua Dockerfile nên **cần đúng file này có mặt trong repo** — đã thêm 1
dòng ngoại lệ `!models/best.onnx` vào cuối `.gitignore` (chỉ ngoại lệ đúng
1 file, các rule chung khác giữ nguyên), rồi track file đó qua **Git LFS**
(xem "Cách bạn tự test") thay vì commit binary 12MB vào git thường.

## Việc cụ thể

**T9.1 — Chốt host: Render (backend) + Cloudflare Pages (frontend),
tách 2 origin khác nhau.** Cả hai đều free, không cần thẻ. Vì tách origin
(không cùng domain), bắt buộc dùng CORS thật (khác phương án VPS gộp
1-process trước đó) — `ALLOWED_ORIGINS` trên Render phải set đúng URL
Cloudflare Pages.

**T9.1b — bỏ qua (optional, buffer-cuttable theo PLAN.md):** không cần HF
Hub.

**T9.2 — HTTPS: có sẵn, không cần tự set up.** Cả Render lẫn Cloudflare
Pages đều tự cấp HTTPS cho domain mặc định của họ (`*.onrender.com`,
`*.pages.dev`) — không cần Caddy/Let's Encrypt cho phương án này (khác
phương án VPS).

**T9.3 — Hỗ trợ tách origin FE/BE trong code:**
- `web/index.html`: thêm hằng `BACKEND_URL` tường minh ở đầu `<script>`
  (mặc định `""`) — set thành URL Render thật (vd
  `"https://yoga-pose-api.onrender.com"`) trước khi Cloudflare Pages build
  trang. `API_BASE` giữ nguyên logic tự nhận diện `:8080` cho dev local,
  còn lại dùng `BACKEND_URL`.
- `app/main.py`: **không đổi** — `ALLOWED_ORIGINS` env đã có sẵn từ lần
  viết trước, chỉ cần set đúng giá trị lúc deploy Render (URL Cloudflare
  Pages thật) thay vì để mặc định `"*"`.
- `StaticFiles` mount ở `app/main.py` **vẫn giữ nguyên** (không gỡ) — dùng
  cho dev local 1-process và cho việc tự test nhanh bằng cách mở thẳng URL
  Render (không qua Cloudflare Pages) mà không cần set `BACKEND_URL`
  (same-origin tự động đúng).

**T9.4 — Deploy thật (external, cần tài khoản Render + Cloudflare):**
1. **Render:** tạo tài khoản (không cần thẻ), New → Web Service → connect
   GitHub repo này → Render tự nhận diện `Dockerfile` → chọn instance
   **Free** → set env `ALLOWED_ORIGINS` tạm thời `"*"` (sẽ siết lại ở bước
   4) → Deploy. Chờ build xong, lấy URL dạng
   `https://<tên-service>.onrender.com`.
2. **Model cho Render build:** repo GitHub chính gitignore
   `models/*.onnx` nên Render (build thẳng từ GitHub) sẽ không thấy file
   này — dùng **Git LFS** để track `models/best.onnx` thật trong git (xem
   lệnh ở "Cách bạn tự test"), Render tự hỗ trợ LFS khi build.
3. **Cloudflare Pages:** tạo tài khoản (không cần thẻ), Pages → Create
   project → connect repo GitHub này → Build command: để trống (không có
   build step) → Build output directory: `web` → Deploy. Lấy URL dạng
   `https://<project>.pages.dev`.
4. Sửa `web/index.html` dòng `BACKEND_URL` thành đúng URL Render ở bước 1,
   commit + push (Cloudflare Pages tự redeploy khi có push mới).
5. Vào lại Render Settings → Environment, sửa `ALLOWED_ORIGINS` thành đúng
   URL Cloudflare Pages ở bước 3 (siết CORS đúng domain thật).

**T9.5 — Test camera trên iPhone thật (external, cần thiết bị + đã deploy
xong):** mở URL Cloudflare Pages (`https://<project>.pages.dev`) trên
Safari iPhone thật, thử tab Camera trực tiếp — xác nhận HTTPS công khai đủ
điều kiện `getUserMedia()` hoạt động. **Lưu ý cold start:** nếu Render đã
ngủ (free tier ngủ sau ~15 phút không dùng), request `/predict` đầu tiên
sẽ chậm (~30-50s) trong lúc Render khởi động lại container — mở thử 1 lần
trước khi quay video/test thật để "đánh thức" trước.

## File/module liên quan

- `web/index.html` (`BACKEND_URL` mới)
- `app/main.py` (không đổi — CORS/mount đã sẵn từ lần viết trước)
- `Dockerfile` (dùng chung cho cả Render lẫn phương án VPS thay thế)
- `.gitignore` (thêm ngoại lệ `!models/best.onnx` cho đúng 1 file, track
  qua Git LFS — Render cần thấy model thật lúc build từ GitHub repo)
- `README.md` (mục "Deploy" — Render + Cloudflare Pages là chính)

## Bằng chứng / số liệu kỳ vọng

- Local: `uvicorn app.main:app --reload` → `http://localhost:8000/` vẫn
  hoạt động đúng như trước (không đổi).
- Deploy thật: `GET https://<render-url>/health` → `{"status":"ok"}`;
  trang `https://<pages-url>` gọi `/predict` thành công (không lỗi CORS
  trong console), kết quả khớp Giai đoạn 7 (`tree`, conf 0.92).
- T9.5: bạn xác nhận bằng mắt trên iPhone thật.

## Cách bạn tự test sau khi tôi xong

1. **Local trước (mình verify được ở đây):** `uvicorn app.main:app
   --reload`, mở `http://localhost:8000/` — không đổi so với trước.
2. **Đưa `models/best.onnx` vào git bằng LFS** (`.gitignore` đã có sẵn
   ngoại lệ `!models/best.onnx` cho đúng file này — chỉ cần làm phần LFS,
   không cần tự sửa `.gitignore` nữa, chỉ làm 1 lần):
   ```bash
   git lfs install
   git lfs track "models/best.onnx"
   git add .gitattributes models/best.onnx
   git commit -m "Track models/best.onnx qua Git LFS cho Render build"
   git push
   ```
3. **Deploy Render** (dashboard render.com) — theo đúng bước T9.4.1/2 ở
   trên, lấy URL.
4. **Deploy Cloudflare Pages** (dashboard pages.cloudflare.com) — theo
   đúng bước T9.4.3, lấy URL.
5. Sửa `web/index.html` → `BACKEND_URL = "<url-render-thật>"`, commit,
   push. Sửa `ALLOWED_ORIGINS` trên Render → `<url-pages-thật>`.
6. Mở `https://<pages-url>` — test upload ảnh + camera trên máy thường,
   xem Console (F12) không có lỗi CORS.
7. Test lại trên iPhone thật (T9.5) — báo lại kết quả.

## ❓ Quyết định cần bạn chốt

Không có — Render + Cloudflare Pages đã được bạn chọn qua trao đổi, không
còn tradeoff cần cân nhắc thêm cho phương án chính.

## Rủi ro / điều cần lưu ý

- **Render free tier ngủ sau ~15 phút không dùng** — cold start ~30-50s
  cho request đầu. Không phải bug, nhớ "đánh thức" trước khi demo/quay
  video (xem T9.5).
- **Git LFS trên GitHub free có giới hạn băng thông/dung lượng** (1GB
  storage + 1GB bandwidth/tháng ở gói free tính đến lúc viết) —
  `best.onnx` 12MB, dùng thử vài lần deploy là ổn, nhưng nếu build đi build
  lại nhiều lần trong tháng có thể chạm giới hạn bandwidth free của LFS;
  nếu gặp lỗi liên quan LFS quota lúc Render build, đó là nguyên nhân, báo
  lại để mình tìm cách khác (vd Render Disk hoặc tải model qua URL lúc
  container khởi động thay vì bake vào image).
- CORS thật sự cần thiết ở phương án này (khác VPS gộp 1-process) — nếu
  quên set `ALLOWED_ORIGINS` đúng URL Cloudflare Pages ở bước T9.4.5,
  trình duyệt sẽ chặn request `/predict` (lỗi CORS trong Console), không
  phải lỗi backend.
- CPU-only, latency gần số đã đo Giai đoạn 7 (~245ms/ảnh) — đã xác nhận đủ
  dùng.
- `mediapipe==0.10.21` pin cứng — Render dùng Linux amd64, có wheel sẵn,
  không lo lặp lại lỗi ARM/Windows trước đó.

## Phương án thay thế: VPS + Caddy (đã build + review xong, chưa dùng)

Nếu Render free không đủ ổn định (cold start gây khó chịu lúc demo, hoặc
LFS quota vướng), có sẵn phương án dùng VPS riêng của bạn (domain
`hldhn.com`, có thể dùng subdomain `cv.hldhn.com`):

- `docker-compose.yml` + `Caddyfile` ở repo root — Caddy tự xin HTTPS thật
  qua Let's Encrypt cho domain thật, `app` service không public trực tiếp
  (chỉ Caddy 80/443 public), `reverse_proxy app:8000`.
- Deploy: `rsync` code (không có dấu `/` sau tên thư mục — xem ghi chú
  trong `README.md`, tránh bug rsync đổ nội dung lệch chỗ) lên VPS, tạo
  `.env` với `DOMAIN=cv.hldhn.com`, `docker compose up -d --build`.
- Ưu điểm so với Render free: không cold start, không giới hạn LFS
  bandwidth (model copy thẳng qua rsync, không qua git).
- Đã review 2 vòng `cv-architecture-review` sạch, `docker compose config`
  test thật xác nhận wiring env-var đúng — xem "Implementation notes" bên
  dưới, phần ghi ngày trước khi đổi sang Render.

## Implementation notes

**Vòng 1 (HF Spaces → VPS):** viết xong `Dockerfile`, mount static 1-process
(`app/main.py`), `API_BASE` tự nhận diện (`web/index.html`), CORS qua env
`ALLOWED_ORIGINS`. Review 2 vòng `cv-architecture-review`: vòng 1 tìm 1 lỗi
nhỏ (`ALLOWED_ORIGINS.split(",")` không strip khoảng trắng — đã sửa thành
`[o.strip() for o in _allowed_origins.split(",") if o.strip()]`), vòng 2
sạch. Smoke test thật: `GET /health` → ok, `GET /` → đúng trang demo,
`POST /predict` ảnh thật → đúng kết quả (`tree`, conf 0.92) — cả 3 qua
cùng 1 process `uvicorn`. Docker build thật không verify được (Docker
Desktop engine không chạy trong môi trường này).

**Vòng 2 (VPS → Render + Cloudflare Pages):** viết `docker-compose.yml` +
`Caddyfile` cho VPS trước (xong, review 2 vòng sạch — vòng 1 tìm 1 bug
thật: lệnh `rsync` dùng dấu `/` sau tên thư mục làm đổ nội dung lệch chỗ,
đã sửa ở cả `README.md` và spec; kèm 1 nit comment sai gán nhầm việc set
header `Origin` cho Caddy, đã sửa). `docker compose --env-file ... config`
chạy thật xác nhận wiring `${DOMAIN}`/`{$DOMAIN}` đúng.

Sau đó bạn hỏi có host free không (đỡ tốn VPS) → so sánh Oracle (cần thẻ)
vs Render (không cần thẻ) → chọn tách FE/BE: Render + Cloudflare Pages.
Đã sửa `web/index.html` thêm `BACKEND_URL` tường minh (giữ nguyên
`API_BASE` local-dev heuristic, không đổi hành vi dev local). `app/main.py`
không cần đổi gì thêm (CORS/mount đã đủ linh hoạt từ vòng 1). Chưa chạy
lại `cv-architecture-review` cho riêng thay đổi `BACKEND_URL` này (thay
đổi nhỏ, 1 dòng hằng số + 1 dòng logic, cùng pattern đã review kỹ ở vòng
1) — nếu muốn chắc chắn hơn, có thể yêu cầu review thêm 1 vòng trước khi
commit.

**Lỗi thật gặp khi deploy Render (không phải bug review bỏ sót — môi trường
review này không chạy được Docker thật, xem ghi chú Docker build ở vòng 1):**
1. Lần build đầu tiên chạy Python 3.14 (native runtime Render tự chọn thay
   vì Docker) → `mediapipe==0.10.21` không có wheel cho 3.14 → build fail.
   Nguyên nhân: Render auto-detect nhầm "Python" thay vì "Docker" runtime
   dù repo có `Dockerfile` (có thể do repo cũng có `requirements.txt`).
   Không phải lỗi code — hướng dẫn bạn tạo lại Web Service, chọn đúng
   Environment **Docker** trong lúc setup.
2. Sau khi build đúng bằng Docker (`python:3.11-slim`): `ImportError:
   libGL.so.1: cannot open shared object file` lúc import `cv2` —
   `opencv-python-headless` vẫn link `libGL` dù là bản "headless", mà
   base image slim không có sẵn thư viện đồ hoạ hệ thống này. Đây là lỗi
   kinh điển, đã biết cách sửa chuẩn cộng đồng: thêm
   `apt-get install -y libgl1 libglib2.0-0` vào `Dockerfile` trước bước
   `pip install`. Đã sửa, nhưng **không verify build lại được thật** ở môi
   trường này (Docker Desktop engine vẫn không chạy) — cần bạn xác nhận
   qua lần Render tự rebuild sau khi push.

**Deploy Render thành công — xác nhận thật qua `curl`:** `GET /health` →
`{"status":"ok"}`, `POST /predict` ảnh thật → đúng kết quả (`tree`, conf
0.92, `form_ok=true`), khớp Giai đoạn 7. **Latency thật cao hơn nhiều so
với local** — 5 lần gọi liên tiếp: 8401ms, 5790ms, 6616ms, 5154ms, 4512ms
(so với ~245ms CPU local Giai đoạn 7) — do CPU bị giới hạn/chia sẻ mạnh
trên free tier Render, không phải lỗi code (kết quả đúng, chỉ chậm). Đã
trao đổi, bạn chọn chấp nhận (đủ dùng cho demo nộp bài — upload ảnh ok,
camera trực tiếp sẽ giống chụp ảnh mỗi ~5s thay vì mượt). Phương án VPS +
Caddy (không bị throttle) vẫn giữ sẵn trong repo nếu sau này cần đổi lại.

**Deploy Cloudflare Pages + CORS — xác nhận thật:** Cloudflare Pages ban
đầu tự phát hiện `requirements.txt` ở gốc repo và cố `pip install` (do
tính năng Pages Functions auto-detect Python) → dính đúng lỗi mediapipe
version như Render — sửa bằng cách đổi **Root directory** của Pages
project thành `web` (loại `requirements.txt` khỏi tầm nhìn build, không
sửa code). Sau khi set `BACKEND_URL` trong `web/index.html` = URL Render
thật và `ALLOWED_ORIGINS` trên Render = URL Cloudflare Pages thật
(`https://computer-vision-project.pthieu290998.workers.dev`), verify qua
`curl` thật:
- `OPTIONS /predict` với `Origin` đúng domain Cloudflare Pages → header
  `access-control-allow-origin` khớp đúng domain đó (không còn `*`).
- `POST /predict` ảnh thật kèm `Origin` đúng → 200 OK, CORS header đúng.
- `OPTIONS /predict` với `Origin` giả (domain lạ) → không có header
  `access-control-allow-origin` — xác nhận CORS chặn đúng domain không
  được phép, không phải lỗi cấu hình quá lỏng.

**T9.5 — bug thật phát hiện khi test trên iPhone:** camera streaming bình
thường nhưng không bao giờ hiện result, hoàn toàn im lặng (không có lỗi
gì hiện ra). Chẩn đoán: Render free tier ngủ lại sau ~15 phút không dùng —
request đầu tiên sau khi ngủ có thể cold-start rất lâu (lâu hơn nhiều so
với số ~5-8s đã đo lúc service vừa build xong, chưa từng ngủ hẳn); trong
lúc đó biến `inFlight` chặn đúng như thiết kế (tránh dồn request), nhưng
không có UI nào báo "đang xử lý" — nhìn giống hệt bị treo dù thực ra chỉ
đang chờ phản hồi chậm. Đã sửa `web/index.html`:
- `camStatus` hiện "Đang gửi khung hình lên server..." trong lúc chờ, trả
  về "Camera đang chạy..." khi xong.
- Thêm `AbortController` timeout 60s — nếu thật sự treo/lỗi mạng, sẽ báo
  rõ thay vì chờ vô hạn.
- Thêm guard bỏ qua lượt capture nếu `videoWidth`/`videoHeight` bằng 0
  (edge case một số trình duyệt mobile chưa kịp có metadata video).
Chưa verify lại được trên iPhone thật sau fix (cần bạn test lại) —
chỉ verify được cú pháp JS không lỗi qua Playwright (console sạch, chỉ có
warning 404 favicon vô hại đã biết từ trước).

**T9.5 — bug thật thứ 2 (nguyên nhân đúng, xác nhận qua screenshot thật
từ bạn):** "im lặng không kết quả" ở trên là chẩn đoán sai hướng — nguyên
nhân thật là iOS Safari đẩy `<video>` nguồn `getUserMedia` (MediaStream)
vào **native fullscreen video player** (UI có nút đóng, Picture-in-Picture,
mute, pause, badge "LIVE", thanh tua) thay vì phát inline trong trang —
`<canvas>` overlay của mình vẫn đúng vị trí bên dưới, chỉ bị lớp UI native
này che khuất hoàn toàn, khớp đúng mô tả "phải thoát chế độ broadcast mới
thấy khung đỏ". Đây là bug WebKit đã biết: `playsinline` chuẩn đôi khi
không đủ cho nguồn MediaStream trên 1 số bản iOS Safari. Đã sửa
`web/index.html`:
- Thêm attribute `webkit-playsinline` (cú pháp cũ, vẫn cần cho tương
  thích), `disablePictureInPicture`, `disableRemotePlayback`.
- Set `camVideo.playsInline = true` và `camVideo.muted = true` qua thuộc
  tính JS (không chỉ HTML attribute) **trước** khi gán `srcObject`.
Verify cú pháp JS qua Playwright (console sạch) — chưa verify được hành vi
thật trên iPhone (cần bạn test lại, không có thiết bị thật ở môi trường
này).

**Việc còn lại — hoàn toàn external, cần bạn tự làm:** Git LFS cho
`models/best.onnx`, tạo tài khoản + deploy Render, tạo tài khoản + deploy
Cloudflare Pages, set `BACKEND_URL`/`ALLOWED_ORIGINS` chéo nhau đúng URL
thật, test end-to-end, cuối cùng T9.5 (iPhone thật). Xem "Cách bạn tự
test" ở trên cho từng bước cụ thể.

**Review vòng 3 (sau khi thêm `BACKEND_URL`):** vòng 1 tìm 1 lỗi thật —
`.gitignore` chặn `models/best.onnx` qua 2 rule chung (`models/*`, `*.onnx`)
nhưng hướng dẫn Git LFS ở `README.md`/spec lại không đề cập cần ngoại lệ
gì, hoặc đề cập sai cách ("bỏ *.onnx khỏi .gitignore" — sẽ un-ignore toàn
bộ file .onnx, không chỉ 1 file cần) — verify thật bằng `git add -n
models/best.onnx` (fail trước khi sửa). Đã sửa: thêm đúng 1 dòng
`!models/best.onnx` vào cuối `.gitignore` (giữ nguyên mọi rule khác, các
`.pt`/`.onnx` khác vẫn bị ignore — verify lại bằng file test thật, xoá
sau khi verify xong), đồng bộ lại lệnh Git LFS ở cả `README.md` và spec.
Vòng 2: sạch, chỉ còn 1 nit (comment cũ trong `app/main.py` nhắc "Space
secrets" từ thời HF Spaces, sửa lại thành "Render Environment settings").
Đã sửa nit đó, smoke test lại `curl /health` + `curl /` xác nhận server
local vẫn chạy đúng sau tất cả thay đổi.
