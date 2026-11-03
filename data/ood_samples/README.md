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

Ở Giai đoạn 5 chưa có ảnh cho `bridge`/`shoulderstand` (dataset trên không có
2 lớp này) — đã bổ sung ở Giai đoạn 12, xem mục dưới.

## Bổ sung Giai đoạn 12 (T12.4) — Wikimedia Commons

**Nguồn:** Wikimedia Commons, các category `Setu_Bandhasana` (bridge),
`Sarvangasana` (shoulderstand), `Vrikshasana` (tree), `Adho_Mukha_Svanasana`
(downdog), `Phalakasana` (plank). Chỉ lấy ảnh license CC0 / Public domain /
CC BY / CC BY-SA; tác giả + license + link từng ảnh trong
`commons_sources.csv` (CC BY yêu cầu ghi công). Tên file `commons_<pageid>.jpg`,
ảnh thumbnail 960px.

**Chọn tay** sau khi xem từng ảnh: bỏ tranh vẽ, ảnh ghép nhiều khung, biến thể
khác tư thế (một chân, chaturanga, halasana), lớp tập quá đông người. Giữ lại
vài ảnh nhiều người cùng tư thế và ảnh scan đen trắng như ca khó có chủ đích.

**Kiểm tra không trùng Roboflow:** mỗi ảnh được so với cả 1013 ảnh của
`data/raw/yoga_v1` bằng đúng tín hiệu của `src/data/dedup_split.py`
(dHash 16×16 kể cả lật, ngưỡng 12; ORB+RANSAC, ngưỡng 25 inlier). Không ảnh
nào có dHash ≤ 12 (gần nhất: 42). 4 ảnh vượt ngưỡng ORB (25–53 inlier) được xem
tận mắt: đều là khớp giả (ảnh scan nhiễu hạt sinh nhiều keypoint) — tư thế,
người, bối cảnh khác hẳn, nên vẫn giữ.

**Số lượng sau bổ sung:** 45 ảnh — bridge 8, shoulderstand 9, tree 9,
downdog 10, plank 9 (= 18 ảnh Kaggle cũ + 27 ảnh Commons).

**Còn thiếu:** ảnh tự chụp bằng điện thoại (đúng loại ảnh người dùng gửi lên
PROD) — chưa có.
