# Spec — g10. Tài liệu & Slide (rubric: "Sản phẩm nộp" — README, sơ đồ, slide)

**Plan source:** `docs/PLAN.md` — Giai đoạn 10
**Status:** implemented <!-- T10.1-T10.5 xong, xem Implementation notes -->

## Mục tiêu

Chuyển toàn bộ tài liệu dự án từ trạng thái "kế hoạch/scaffold" sang phản
ánh đúng những gì đã làm thật (Giai đoạn 0-9 đều đã xong với số liệu thật
có sẵn) — đây là bước tổng hợp lại, không phát sinh code/số liệu mới.
Nguồn số liệu thật đã có rải rác trong `docs/problem_statement.md` (từng
mục Giai đoạn 1-5, 7) và các spec `docs/specs/g*.md` — không bịa số liệu
mới, chỉ tổng hợp lại.

## Việc cụ thể

**T10.1 — Viết lại README:**
- Bỏ dòng "Đang ở giai đoạn khởi tạo scaffold" ở mục "Trạng thái" (không
  còn đúng) — thay bằng tóm tắt kết quả thật: mAP baseline/ablation
  (Giai đoạn 2-3), OOD accuracy 94.4% (Giai đoạn 5), latency ONNX CPU/GPU
  (Giai đoạn 7), URL demo live (Render + Cloudflare Pages, Giai đoạn 9).
- Thêm mục "Kết quả" ngắn gọn (bảng hoặc bullet, số liệu thật đã có sẵn
  trong `docs/problem_statement.md`, không đo lại).
- Thêm link tới demo live thật:
  `https://computer-vision-project.pthieu290998.workers.dev`.
- Giữ nguyên các mục Kiến trúc/Cấu trúc thư mục/Setup/Chạy lại từ
  đầu/Deploy đã đúng từ trước (không viết lại từ đầu, chỉ bổ sung).

**T10.2 — Sơ đồ kiến trúc + luồng xử lý end-to-end:**
- Dùng skill `arch-diagram` có sẵn (tạo/cập nhật `docs/architecture.md`
  với sơ đồ Mermaid) — đúng công cụ được thiết kế riêng cho việc này,
  không tự vẽ tay lại.
- Xác nhận sơ đồ phản ánh đúng kiến trúc 2 lớp thật (YOLOv8 ONNX detect +
  classify → crop → MediaPipe Pose → rule-based angle scoring) và luồng
  deploy thật (Cloudflare Pages frontend → Render backend, CORS qua
  `ALLOWED_ORIGINS`).

**T10.3 — Điền đầy đủ `docs/problem_statement.md`:**
- Đã có: Bài toán, Requirement, Kiến trúc 2 lớp, Dataset, Training
  baseline, Ablation, Evaluation & Error Analysis, Feedback loop (GĐ5),
  Export & Backend (GĐ7) — **giữ nguyên, không sửa nội dung đã đúng**.
- Thiếu, cần thêm 2 mục mới (nối tiếp đúng thứ tự Giai đoạn):
  - **"Form scoring rule-based (Giai đoạn 6)"** — tóm tắt cách hiệu chỉnh
    `POSE_RULES` bằng số đo thật trên 15 ảnh mẫu (3/lớp × 5 lớp), kết quả
    test thủ công (14/15 ảnh đúng form + 5/5 case tổng hợp lệch góc), 2
    giới hạn thật đã ghi nhận (MediaPipe kém với pose lộn ngược nền tương
    phản thấp; góc 2D bị méo khi camera chụp xiên) — lấy từ
    `docs/specs/g6-form-scoring.md` + `data/pose_rule_samples/README.md`,
    không đo lại.
  - **"Web demo & Deploy public (Giai đoạn 8-9)"** — tóm tắt kiến trúc
    tách frontend/backend (Cloudflare Pages + Render), 2 bug thật gặp và
    sửa khi test iPhone (iOS native fullscreen player che overlay; cold
    start Render gây "im lặng không kết quả"), xác nhận FR7 hoàn thành
    qua test camera iPhone thật — lấy từ `docs/specs/g9-deploy-public.md`,
    không đo lại.

**T10.4 — Slide tóm tắt (`docs/slides/`):**
- Format: 1 file Markdown (`docs/slides/summary.md`) theo cấu trúc slide
  (mỗi `---` là 1 slide, tương thích Marp/reveal.js nếu cần convert sau) —
  nhanh, không cần công cụ thiết kế riêng, đủ cho việc trình bày/quay
  video Giai đoạn 11.
- Nội dung bám đúng khung video outline đã định ở PLAN.md T11.1: bài toán
  → dữ liệu → cách làm → kết quả → lỗi & bài học → demo. ~10-12 slide,
  số liệu thật lấy từ `problem_statement.md` sau khi T10.3 xong.

**T10.5 — Đánh dấu `docs/requirement_checklist.md`:**
- Tick `[x]` cho 7 mục bắt buộc (1-7) — đã có số liệu/link chứng minh thật
  cho từng mục sau T10.1-T10.4, không mục nào còn thiếu bằng chứng.
- Tick "Sản phẩm nộp" (repo public, code, README, sơ đồ, tài liệu 7 mục,
  slide) — **trừ** dòng "Video trình bày 5-10 phút" (Giai đoạn 11, chưa
  làm) — để trống dòng đó.

## File/module liên quan

- `README.md`
- `docs/architecture.md` (mới, qua skill `arch-diagram`)
- `docs/problem_statement.md`
- `docs/slides/summary.md` (mới)
- `docs/requirement_checklist.md`

## Bằng chứng / số liệu kỳ vọng

Không có số liệu mới — bằng chứng là tính đầy đủ/nhất quán giữa các file
tài liệu và số liệu thật đã tồn tại từ Giai đoạn 0-9 (đối chiếu qua nhau
được, không mâu thuẫn).

## Cách bạn tự test sau khi tôi xong

1. Đọc lại `README.md` từ đầu như một người lạ mới clone repo — xác nhận
   đủ để hiểu dự án + chạy lại được, không còn chỗ nào ghi "đang thiết
   kế"/"scaffold".
2. Mở `docs/architecture.md` — xác nhận sơ đồ Mermaid render đúng, khớp
   kiến trúc thật.
3. Đọc lướt `docs/problem_statement.md` — xác nhận đủ 7 mục rubric, không
   chỗ nào còn là "kế hoạch" thay vì "kết quả".
4. Mở `docs/slides/summary.md` — xác nhận đủ nội dung dùng làm dàn ý quay
   video Giai đoạn 11.
5. Xem `docs/requirement_checklist.md` — xác nhận đã tick đúng, không tick
   nhầm mục chưa làm (video Giai đoạn 11 vẫn để trống).

## ❓ Quyết định cần bạn chốt

Không có — nguồn số liệu đều có sẵn thật, không có tradeoff cần chọn.

## Rủi ro / điều cần lưu ý

- Đây là bước tổng hợp, không phải bước tạo số liệu mới — nếu trong lúc
  viết phát hiện số liệu ở 2 chỗ khác nhau không khớp nhau (vd
  `problem_statement.md` vs spec gốc), sẽ dừng lại hỏi thay vì tự chọn số
  nào đúng.
- `docs/slides/summary.md` là Markdown thô, chưa phải slide đẹp trình
  chiếu được (vd PowerPoint/Google Slides) — nếu bạn cần định dạng đó,
  đây chỉ là nội dung/dàn ý, cần convert thêm (Marp CLI hoặc paste tay).

## Implementation notes

**Không đo số liệu mới** — đúng như dự kiến, chỉ tổng hợp lại số liệu
thật đã có sẵn từ Giai đoạn 0-9 (không phát hiện mâu thuẫn nào giữa các
nguồn khi viết).

**T10.1 — README:** bỏ dòng "Đang ở giai đoạn khởi tạo scaffold", thêm
mục "Kết quả" (bảng tóm tắt 7 giai đoạn + link demo live), cập nhật
"Trạng thái" phản ánh đúng đã xong Giai đoạn 0-9.

**T10.2 — `docs/architecture.md`:** dùng skill `arch-diagram`, viết mới
(chưa có file trước đó). 4 sơ đồ Mermaid: (1) kiến trúc model 2 lớp
(graph TD, có chú thích màu train/pretrained/rule-based), (2) luồng
request end-to-end thật (sequenceDiagram, phản ánh đúng
`PoseDetectionService`/lazy-load/CORS thật, không phải bản dự kiến), (3)
luồng dữ liệu/training (graph TD, ghi rõ v2 vẫn là code stub
`NotImplementedError`, không giả vờ đã chạy), (4) deploy topology thật
(graph LR, Cloudflare Pages + Render + phương án thay thế VPS).

**T10.3 — `docs/problem_statement.md`:** thêm 2 mục mới ("Form scoring
rule-based — Giai đoạn 6", "Web demo & Deploy public — Giai đoạn 8-9"),
lấy nguyên số liệu từ `docs/specs/g6-form-scoring.md` và
`docs/specs/g9-deploy-public.md` (không đo lại). Tiện thể sửa 1 câu lỗi
thời ở mục Giai đoạn 7 (nhắc "Hugging Face Spaces" — kế hoạch deploy ban
đầu đã đổi sang Render/Cloudflare Pages từ Giai đoạn 9, quên cập nhật lúc
đó) thành đúng số liệu CPU thật đã đo.

**T10.4 — `docs/slides/summary.md`:** 12 slide Markdown (`---` phân
cách), bám đúng khung video outline PLAN.md T11.1 (bài toán → dữ liệu →
cách làm → kết quả → lỗi & bài học → demo → liên kết).

**Bổ sung theo yêu cầu (sau khi user hỏi "có làm được Slide không"):**
dựng thêm `docs/slides/presentation.html` — bản trình chiếu thật (13
slide, cùng nội dung với `summary.md`, khác định dạng: HTML tự chứa,
điều hướng bằng phím mũi tên/nút bấm, có thanh tiến trình + bộ đếm, không
cần server/build step, mở trực tiếp bằng trình duyệt hoặc double-click).
Thiết kế riêng cho chủ đề (không dùng theme AI-generic): nền sage-bone
nhạt, mực forest-charcoal, font Fraunces (heading)/IBM Plex Sans
(body)/IBM Plex Mono (data/nhãn) — cặp màu xanh lá/cam đỏ dùng đúng như
màu box thật trong `web/index.html` (form_ok true/false), motif ngoặc
vuông kiểu nhãn bounding-box cho eyebrow mỗi slide. Preview thật qua
Artifact trước khi đưa vào repo, sau đó copy vào `docs/slides/presentation.html`
+ thêm `<meta charset>`/`<meta viewport>` (không có sẵn khi ở dạng
Artifact — cần cho file đứng độc lập ngoài môi trường Artifact).

**T10.5 — `docs/requirement_checklist.md`:** tick đủ 7 mục rubric + hầu
hết "Sản phẩm nộp" — **để trống 2 dòng**: "GitHub repo public" (cần bạn
tự xác nhận repo đã set Public trên GitHub, môi trường này không kiểm tra
được) và "Video trình bày" (Giai đoạn 11, chưa làm).

**Smoke test:** không có code để chạy — verify bằng cách xác nhận mọi
file được link tới đều tồn tại thật (`docs/architecture.md`,
`docs/slides/summary.md`, và các spec liên quan) + đối chiếu số liệu
chính (94.4%, 245.8ms, 206.29/247.94ms) xuất hiện nhất quán giữa README,
`problem_statement.md`, slide — không có sai lệch.

**Deferred:** không có — mọi việc T10.1-T10.5 làm được trong môi trường
này, không cần Colab/GPU/tài khoản ngoài (trừ 1 dòng checklist cần bạn tự
xác nhận repo Public, đã ghi rõ ở trên).
