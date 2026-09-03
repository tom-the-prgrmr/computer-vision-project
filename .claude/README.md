# Claude Code tooling cho dự án này

Bộ skill/agent trong `.claude/` để chạy dự án theo `docs/PLAN.md` với vòng
code → review → auto-fix tự động, dừng lại hỏi khi cần quyết định.

## Trước khi dùng lần đầu (và sau mỗi lần sửa `.claude/`)

Danh sách skill/agent được nạp lúc khởi động phiên, **không tự refresh giữa
chừng**. Nếu gõ `/next-step` mà báo "Unknown command", hoặc vừa sửa file
trong `.claude/skills`/`.claude/agents`: đóng terminal, mở lại, chạy `claude`
trong thư mục repo này.

## 4 công cụ

| Lệnh | Loại | Dùng khi |
|---|---|---|
| `/next-step` | Skill | **Vòng lặp chính** — mỗi lần gõ, xử lý trọn 1 bước trong `PLAN.md`: spec → duyệt → code → review → fix |
| `cv-architecture-review` | Agent | Review 1 diff theo luật kiến trúc riêng của dự án (2 lớp YOLO/MediaPipe, rubric mục 5 vs 6...) — `/next-step` tự gọi, cũng gọi tay được khi sửa code ngoài flow |
| `/rubric-status` | Skill | Check nhanh tiến độ 7 mục rubric, bất kỳ lúc nào, không cần đang ở bước nào |
| `/arch-diagram` | Skill | Vẽ/cập nhật `docs/architecture.md` (mermaid) — deliverable bắt buộc khi nộp bài |

## Vòng lặp chính: `/next-step` — đúng 2 bước cho bạn

```
/next-step                # tự tìm bước hiện tại trong PLAN.md
/next-step g6             # chỉ định thẳng Giai đoạn 6
```

Gọi 2 lần liên tiếp cho mỗi bước, mỗi lần làm 1 việc:

**Lần gọi thứ nhất (chưa có spec)** — viết `docs/specs/g<N>-<slug>.md` bám
theo đúng nội dung Giai đoạn đó trong `PLAN.md` (không bịa), chốt cụ thể chỗ
PLAN.md để ngỏ (vd "epochs baseline (vd 50)" → 1 con số thật), rồi **dừng
lại luôn** — không hỏi gì, không cần bạn gõ "ok". Đây là lúc **bạn tự đọc
file spec** đó.

**Lần gọi thứ hai (spec đã có)** — code theo spec → gọi agent
`cv-architecture-review` → tự fix mọi finding → review lại 1 lần nữa →
**chạy smoke test** (import/syntax check, gọi hàm với dữ liệu mẫu,
`TestClient`/`curl` cho API — tuỳ cái gì thật sự chạy được trong môi trường
này) → tick `[x]` task đã xong trong `PLAN.md` → báo cáo kèm **hướng dẫn cụ
thể để bạn tự test thật** (curl mẫu, URL mở trình duyệt, "chạy cell X trên
Colab", "thử camera trên điện thoại"...).

Nó chỉ **dừng lại hỏi bạn** (không đoán, không tự chọn) khi:

- Spec có mục "❓ Quyết định cần bạn chốt" không rỗng.
- Đang code mà gặp lựa chọn không có trong spec (tham số mơ hồ, thiếu input...).
- Cả bước hiện tại chỉ toàn việc ngoài tầm code (tạo tài khoản Roboflow, bật
  Colab Secret, chạy cell trên Colab...) — nó liệt kê việc bạn cần tự làm rồi
  dừng, không bịa việc để "trông có tiến triển".

Trả lời thẳng trong chat khi nó hỏi, nó tiếp tục luôn cùng lượt.

**Không bao giờ tự `git commit`/`push`** — luôn để working tree ở trạng thái
chưa commit, bạn tự xem `git diff` và commit khi ưng ý.

## Chạy lặp không cần gõ tay: `/loop /next-step`

```
/loop /next-step
```

Skill `/loop` (có sẵn, không cần restart) sẽ tự gọi lại `/next-step` theo
nhịp tự căn (không cần đặt interval). Vì `/next-step` đã tự dừng hỏi ở đúng
chỗ cần quyết định hoặc việc ngoài code, loop này không chạy tuột qua — nó
sẽ đứng chờ bạn trả lời/làm xong rồi mới đi tiếp. Dừng loop: gõ lại `/loop`
với lệnh dừng, hoặc Ctrl+C.

## Dùng lẻ (ngoài vòng lặp chính)

- `/rubric-status` — trước khi báo cáo tiến độ, hoặc gần deadline muốn biết
  còn thiếu gì trong 7 mục + phần "Sản phẩm nộp".
- `/arch-diagram` — chạy tay bất cứ khi nào kiến trúc/luồng đổi nhiều mà
  chưa tới lúc `/next-step` chạm Giai đoạn 10 (Tài liệu & Slide).
- Gọi `cv-architecture-review` qua Agent tool trực tiếp nếu bạn tự sửa code
  tay (không qua `/next-step`) và muốn kiểm tra riêng phần kiến trúc.

## File các skill tự sinh/sửa

- `docs/specs/g<N>-<slug>.md` — spec chi tiết từng Giai đoạn, `Status`:
  `draft` (vừa viết, bạn đang đọc) → `implemented` (tự set sau khi code+test
  xong).
- `docs/architecture.md` — sơ đồ mermaid (từ `/arch-diagram`).
- `docs/PLAN.md` — checkbox `[x]` được `/next-step` tự tick khi task xong.
- `docs/requirement_checklist.md` — **không** bị tự sửa, `rubric-status` chỉ
  báo cáo, không đụng vào trừ khi bạn yêu cầu.

## Ví dụ 1 vòng thực tế

```
> /next-step
  → "Đang ở Giai đoạn 1 (Data), chưa có spec — đã viết docs/specs/g1-data.md, đọc rồi gọi lại nhé."
  (bạn tự mở file đọc)
> /next-step
  → chạy T1.1–T1.6 (script + notebook), review, auto-fix, smoke test
  → "Xong. Muốn test thật: mở notebooks/01_data_exploration.ipynb, chạy hết
     cell, kiểm tra data/raw/yoga_v1/ có train/valid/test + data.yaml."
> /next-step
  → "Giai đoạn 2 (Baseline training)..." tiếp tục tương tự
```
