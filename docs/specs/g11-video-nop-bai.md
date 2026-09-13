# Spec — g11. Video & nộp bài (rubric: "Sản phẩm nộp" — video trình bày)

**Plan source:** `docs/PLAN.md` — Giai đoạn 11
**Status:** implemented <!-- T11.1 xong; T11.2/T11.3/T11.5 cần bạn tự làm; T11.4 gần xong (repo đã Public, xác nhận thật qua gh CLI) -->

## Bối cảnh quan trọng

Đây là bước cuối cùng. 4/5 task hoàn toàn ngoài môi trường này (quay,
edit, push cuối do bạn xác nhận, nộp Classroom) — chỉ **T11.1 (viết kịch
bản chi tiết)** là việc code/tài liệu mình làm được thật ở đây. Mình
không có camera/màn hình của bạn, không quay/edit video được.

Toàn bộ nguyên liệu cho kịch bản đã có sẵn thật, không cần đo/viết gì
mới: `docs/slides/presentation.html` (hoặc `.pptx`) làm khung, số liệu
thật lấy từ `docs/problem_statement.md`.

## Mục tiêu

Có 1 kịch bản nói chi tiết, ước lượng đúng timing 5-10 phút (yêu cầu đề
bài), khớp từng slide/màn hình cụ thể — để bạn cầm kịch bản quay thẳng,
không phải tự nghĩ nội dung lúc quay.

## Việc cụ thể

**T11.1 — Viết kịch bản chi tiết (làm được ở đây):**
- 1 file `docs/slides/script.md` — mỗi đoạn ghi rõ: **slide nào** (khớp
  số thứ tự trong `presentation.html`/`.pptx`), **câu nói cụ thể** (không
  phải gạch đầu dòng ý tưởng — viết thành câu hoàn chỉnh để đọc/nói được
  luôn), và **thời lượng ước lượng** (dựa trên ~2.5 từ/giây tiếng Việt nói
  bình thường).
- Tổng thời lượng cộng dồn phải rơi vào khoảng 5-10 phút (300-600 giây) —
  nếu bản đầy đủ vượt quá, đánh dấu rõ đoạn nào cắt được trước (ưu tiên
  cắt phần nào ít quan trọng nhất theo rubric).
- Bám đúng khung đề bài yêu cầu: bài toán → dữ liệu → cách làm → kết quả
  → lỗi & bài học → demo chạy thật (đã có sẵn trong slide, kịch bản chỉ
  viết lời nói cụ thể cho từng phần).
- Phần "demo chạy thật" (slide 11) ghi rõ **thao tác tay cần làm lúc quay**
  (mở URL nào, bấm nút nào, đợi bao lâu) — không chỉ lời nói.

**T11.2 — Quay (external, bạn tự làm):** ưu tiên quay demo camera trực
tiếp thật trên điện thoại qua URL public
(`https://computer-vision-project.pthieu290998.workers.dev`) — đã xác
nhận chạy đúng ở Giai đoạn 9. Phần trình bày có thể quay màn hình
(share slide) + giọng nói, hoặc xuất hiện trên camera — xem mục ❓ bên
dưới.

**T11.3 — Edit, xuất video 5-10 phút (external, bạn tự làm):** cắt ghép
theo kịch bản T11.1, xuất file.

**T11.4 — Push cuối + xác nhận repo public (chia 2 phần):**
- *Làm được ở đây:* xác nhận working tree sạch (`git status`), không còn
  gì uncommitted trước khi bạn coi là "final push".
- *Cần bạn tự làm:* xác nhận repo GitHub đang **Public** (Settings →
  General → Danger Zone trên GitHub, hoặc mình gợi ý lệnh `gh repo view
  --json visibility` nếu bạn có `gh` CLI đã login) — mình không có quyền
  đổi visibility repo của bạn.

**T11.5 — Nộp Google Classroom (external hoàn toàn):** cần tài khoản
Classroom của bạn, mình không làm thay được.

## File/module liên quan

- `docs/slides/script.md` (mới)
- Nguồn: `docs/slides/presentation.html`, `docs/problem_statement.md`

## Bằng chứng / số liệu kỳ vọng

- `docs/slides/script.md` có timing cộng dồn rơi vào 300-600 giây, khớp
  đủ số slide trong `presentation.html` (13 slide).
- `git status` sạch trước khi báo "sẵn sàng push cuối".

## Cách bạn tự test sau khi tôi xong

1. Đọc `docs/slides/script.md`, thử đọc to 1 đoạn bất kỳ, so tốc độ đọc
   thật của bạn với ước lượng trong file — nếu lệch nhiều, báo lại để
   mình điều chỉnh timing cho sát giọng đọc thật của bạn.
2. Quay theo kịch bản (điện thoại/máy tính), có thể quay nhiều lần cho
   từng đoạn rồi ghép, không cần 1 lần liền mạch.
3. Edit, xuất video, xem lại tổng thời lượng có trong khoảng 5-10 phút.
4. Xác nhận repo Public trên GitHub Settings.
5. Nộp trên Google Classroom kèm link GitHub.

## ❓ Quyết định cần bạn chốt

**Đã chốt:** bạn chọn "chỉ cần video app chạy" — không cần kịch bản đọc
nguyên văn kiểu voice-over/talking-head trang trọng. Đổi cách viết
`script.md` thành **kịch bản demo dạng checklist**: mỗi bước = hành động
cụ thể (mở URL nào, bấm gì, đợi bao lâu) + 1-2 câu gợi ý nói ngắn gọn
(không bắt buộc đọc nguyên văn) + timing ước lượng. Trọng tâm đặt vào
phần demo app chạy thật (thay vì narrate lý thuyết dài dòng qua từng
slide) — các phần bài toán/kiến trúc/kết quả vẫn có mặt nhưng rút gọn
tối đa, chỉ đủ ý để nói khi lướt qua slide, không viết thành văn đầy đủ.

## Rủi ro / điều cần lưu ý

- Timing ước lượng (~2.5 từ/giây) là trung bình — tốc độ nói thật của mỗi
  người khác nhau, cần bạn tự verify ở bước "Cách bạn tự test" #1 trước
  khi quay thật, tránh quay xong mới phát hiện dài/ngắn quá.
- Phần demo (T11.2) phụ thuộc Render free tier — nếu service đã ngủ, nhớ
  mở URL trước ~1 phút để "đánh thức" trước khi bắt đầu quay đoạn đó
  (tránh phải cắt cảnh chờ trong video).

## Implementation notes

**Đổi hướng theo yêu cầu thật:** bạn chốt "chỉ cần video app chạy" thay
vì kịch bản voice-over/talking-head trang trọng như dự kiến ban đầu —
`docs/slides/script.md` viết lại thành dạng **checklist demo-focused**
(hành động cụ thể + ý nói ngắn gọn + timing, không phải văn đọc nguyên
văn), trọng tâm đặt vào mục 6 "Demo app chạy thật" (~2.5-4 phút, phần
lớn nhất trong kịch bản).

**Xác nhận thật trước khi viết kịch bản (Playwright, trên site live):**
test lại tab Upload ảnh trên
`https://computer-vision-project.pthieu290998.workers.dev` — đúng
`plank (88%)`, box vẽ đúng vị trí, xác nhận chức năng vẫn hoạt động
đúng trước khi hướng dẫn bạn quay demo phần này. (Lưu ý: mình không có
công cụ quay video/screen-recording thật trong môi trường này — chỉ
chụp được ảnh tĩnh; bạn hỏi "record 1 vid check upload" lúc đầu, đã làm
rõ giới hạn này và chuyển sang xác nhận bằng Playwright + screenshot
thay thế.)

**T11.4 — xác nhận thật:** `gh repo view --json visibility` → repo đã
**PUBLIC** — không cần bạn làm gì thêm cho phần này. `git status` sạch
trước khi viết note này (chỉ còn `docs/specs/g11-video-nop-bai.md` +
`docs/slides/script.md` chưa commit — sẽ sạch hoàn toàn sau khi bạn
commit/push).

**Deferred (external, đúng như spec dự kiến):** T11.2 (quay), T11.3
(edit + xuất), T11.5 (nộp Classroom) — cần bạn tự làm, không thể làm
thay trong môi trường này.
