# Spec — G0. Setup (rubric: nền tảng cho toàn bộ 7 mục, không tính riêng)

**Plan source:** `docs/PLAN.md` — Giai đoạn 0 (`T0.1`–`T0.5`)
**Status:** draft <!-- draft -> approved (human review) -> implemented (set by implement-spec) -->

## Mục tiêu

Đưa repo + môi trường về trạng thái sẵn sàng cho Giai đoạn 1 (Data): thay
đổi hiện tại đã được review/commit/push, có Roboflow API key khả dụng cả
local (`.env`) lẫn Colab (Secret), Drive đã mount với repo clone vào đó, và
dependencies cài được trong Colab. Đây là giai đoạn hạ tầng — không sinh ra
số liệu/artifact nào cho rubric, chỉ mở khoá các giai đoạn sau.

## Việc cụ thể (từ PLAN.md, đã chốt chi tiết)

- **T0.1 — Review & commit & push thay đổi hiện tại**
  Phạm vi theo `git status` tại thời điểm viết spec này: modified
  `README.md`, `app/main.py`, `docs/problem_statement.md`,
  `docs/requirement_checklist.md`, `web/index.html`; untracked `.claude/`,
  `.env.example`, `docs/PLAN.md`, `docs/REQUIREMENTS.md`.
  Acceptance: `git diff` đã được xem qua (không có gì bất ngờ/không mong
  muốn lẫn vào), 1 commit tạo trên `main` chứa toàn bộ các thay đổi trên,
  `git push origin main` thành công, `git status` sau đó là "working tree
  clean" và "up to date with origin/main". Đây là task duy nhất của GĐ0 làm
  được ngay trong môi trường này — không cần tài khoản/dịch vụ ngoài.
  **Thực hiện bởi:** Claude (cần xác nhận trước khi push, vì push là hành
  động hướng ngoại/khó đảo ngược).

- **T0.2 — Roboflow API key vào `.env` local**
  Acceptance: file `.env` (không commit — đã có trong phạm vi
  `.gitignore`, xác nhận lại) tồn tại ở root repo, copy từ `.env.example`,
  với `ROBOFLOW_API_KEY=<key thật>` điền vào.
  **Thực hiện bởi:** người dùng (cần tài khoản Roboflow + lấy key từ
  https://app.roboflow.com/settings/api — nằm ngoài môi trường CLI này).

- **T0.3 — Colab Secret `ROBOFLOW_API_KEY`**
  Acceptance: trong Colab, mục 🔑 Secrets có entry `ROBOFLOW_API_KEY` với
  giá trị = key ở T0.2, notebook access bật cho notebook sẽ dùng (vd
  `01_data_exploration.ipynb`).
  **Thực hiện bởi:** người dùng (thao tác trong giao diện Colab).

- **T0.4 — Mount Google Drive, clone repo vào Drive**
  Acceptance: trong Colab, `drive.mount('/content/drive')` chạy được, repo
  đã `git clone` vào một thư mục dưới `/content/drive/MyDrive/...` (để
  checkpoint/weights không mất khi session Colab hết hạn).
  **Thực hiện bởi:** người dùng (thao tác trong Colab, ngoài phạm vi CLI
  này).

- **T0.5 — `pip install -r requirements.txt` trong Colab**
  Acceptance: chạy trong Colab, sau đó `import ultralytics; import
  mediapipe` không lỗi. Ghi chú nếu Colab đã có sẵn phiên bản khác gây
  conflict (torch/cuda) thì xử lý riêng, không cần vá trong `requirements.txt`
  trừ khi phát hiện version pin sai.
  **Thực hiện bởi:** người dùng (chạy cell trong Colab).

## File/module liên quan

- Toàn bộ working tree hiện tại (cho T0.1)
- `.env.example` → `.env` (T0.2, không commit `.env`)
- `requirements.txt` (T0.5, chỉ sửa nếu phát sinh lỗi cài đặt)

## Bằng chứng / số liệu kỳ vọng

- T0.1: commit hash mới trên `main`, `git log` cho thấy đã push, `git
  status` sạch.
- T0.2–T0.5: không có artifact trong repo (state sống trong Colab/Drive/
  local `.env`) — xác nhận bằng lời của người dùng là đủ, next-step ở GĐ1
  sẽ tự lộ ra nếu thiếu (vd `download_data.sh` fail vì thiếu key).

## ❓ Quyết định cần bạn chốt

Không có quyết định kỹ thuật mơ hồ ở giai đoạn này. Điều cần chốt là **hành
động**, không phải lựa chọn: T0.2–T0.5 phải làm ngoài môi trường CLI này
(tài khoản Roboflow, giao diện Colab, Google Drive) — Claude không thể thực
hiện thay. Sau khi bạn làm xong 4 việc đó, chạy lại `/next-step` để xác
nhận và chuyển sang Giai đoạn 1.

## Rủi ro / điều cần lưu ý

- Đừng commit `.env` thật — kiểm tra `.gitignore` đã chặn trước khi T0.1
  push.
- `.claude/` (thư mục skill/config của Claude Code) hiện đang untracked —
  xác nhận với người dùng có muốn commit nó vào repo hay thêm vào
  `.gitignore` trước khi push, vì nó ảnh hưởng đến người khác clone repo.
