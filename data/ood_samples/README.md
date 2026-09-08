# OOD samples (Giai đoạn 5)

Ảnh dùng để đo lỗi thật của detector baseline **ngoài phân bố** dataset
Roboflow "YOLO YOGA Dataset" — xem `docs/specs/g5-feedback-loop.md`
(T5.2a/T5.2b).

**Nguồn:** [niharika41298/yoga-poses-dataset](https://www.kaggle.com/datasets/niharika41298/yoga-poses-dataset)
trên Kaggle — 1000 ảnh, 5 lớp (`downdog`, `goddess`, `plank`, `tree`,
`warrior2`), studio background trắng, khác hoàn toàn nguồn Roboflow (khác số
lượng ảnh, khác 2 lớp `bridge`/`shoulderstand`, khác phong cách chụp) nên
hợp lệ làm tập OOD. Dùng cho mục đích học thuật/phi thương mại (bài tập môn
học), không phân phối lại toàn bộ dataset gốc.

**Đã chọn:** 6 ảnh/lớp × 3 lớp (`downdog`, `plank`, `tree` — 3 lớp trùng tên
với model, `goddess`/`warrior2` không dùng vì không khớp lớp nào) từ split
`TEST` của dataset gốc, lấy dàn đều (không phải 6 ảnh đầu liên tiếp) để
tránh trùng góc chụp/outfit. Tổng 18 ảnh, tổ chức theo thư mục con — notebook
`05_feedback_loop_ood.ipynb` tự map `downdog` → `downward` qua
`CLASS_NAME_MAP`.

Chưa có ảnh cho `bridge`/`shoulderstand` — dataset trên không có 2 lớp này.
Có thể bổ sung thủ công (chụp điện thoại hoặc nguồn khác) nếu muốn phủ đủ
5 lớp; không bắt buộc (spec cho phép phủ 3-4/5 lớp).
