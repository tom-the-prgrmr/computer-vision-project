"""Rule-based form scoring: MediaPipe keypoints -> joint angles -> pass/fail + tips.

This is the "phần tự nghĩ thêm" (mục 6) layer. It sits on top of the YOLO
detector's output: for each detected student box, crop it, run MediaPipe Pose
(pretrained, not trained by us) to get 33 landmarks, compute a handful of
joint angles, and compare them against a reference range per pose class.

Not a trained model -> no accuracy/F1 to report here. Document it as a
heuristic layer, validated by spot-checking a few examples manually.
"""

from dataclasses import dataclass
from typing import NamedTuple

import numpy as np

# mediapipe.solutions.pose.PoseLandmark indices we care about, named for
# readability. Fill in the rest as needed per pose.
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_ELBOW, RIGHT_ELBOW = 13, 14
LEFT_WRIST, RIGHT_WRIST = 15, 16
LEFT_HIP, RIGHT_HIP = 23, 24
LEFT_KNEE, RIGHT_KNEE = 25, 26
LEFT_ANKLE, RIGHT_ANKLE = 27, 28

# Bộ 3 landmark (a, b, c) để tính góc tại b, cho mỗi khớp có phân biệt
# trái/phải. score_pose() gộp trái+phải (trung bình) cho khớp đối xứng, hoặc
# chọn động (tree) qua resolve_joint_angle() bên dưới.
JOINT_TRIPLETS: dict[str, tuple[int, int, int]] = {
    "left_hip": (LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE),
    "right_hip": (RIGHT_SHOULDER, RIGHT_HIP, RIGHT_KNEE),
    "left_knee": (LEFT_HIP, LEFT_KNEE, LEFT_ANKLE),
    "right_knee": (RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE),
    "left_elbow": (LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST),
    "right_elbow": (RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST),
}

# Tên khớp đối xứng (không phân trái/phải) mà score_pose() chấp nhận trong
# POSE_RULES -- trung bình góc trái + phải tương ứng trong JOINT_TRIPLETS.
SYMMETRIC_JOINTS = {"hip", "knee", "elbow"}


class AngleRange(NamedTuple):
    joint: str          # e.g. "left_knee"
    min_deg: float
    max_deg: float
    tip: str             # feedback shown to the user if out of range


# Reference ranges per pose class -- hiệu chỉnh bằng số đo thật từ
# scripts/calibrate_pose_rules.py trên 15 ảnh mẫu data/pose_rule_samples/
# (3 ảnh/lớp từ 3 nguồn gốc phân biệt, dataset v1 thật -- xem README trong
# thư mục đó). Mỗi khoảng = [min đo được, max đo được] nới thêm dung sai
# ±15 độ (xem docs/specs/g6-form-scoring.md T6.2 -- số đo thật + log chi
# tiết từng ảnh nằm trong Implementation notes của spec đó). Chỉ 5 lớp thật
# của dataset v1 -- không có "warrior2" (không tồn tại trong data).
POSE_RULES: dict[str, list[AngleRange]] = {
    "tree": [
        AngleRange("standing_knee", 156, 180, "Duỗi thẳng chân trụ hơn."),
        AngleRange("bent_knee", 10, 48, "Mở đầu gối chân co ra ngoài nhiều hơn."),
    ],
    "downward": [
        AngleRange("hip", 34, 81, "Đẩy hông lên cao hơn để tạo hình chữ V ngược rõ hơn."),
        AngleRange("knee", 143, 180, "Duỗi thẳng chân hơn."),
        AngleRange("elbow", 153, 180, "Duỗi thẳng tay hơn, đẩy sàn ra xa."),
    ],
    "plank": [
        # min_deg=159 tính từ 2/3 ảnh mẫu (173.8, 178.7) -- KHÔNG tính ảnh
        # thứ 3 (00000006, đo được hip=119.8, trái/phải đồng nhất ~118-122
        # nên không phải nhiễu detect ngẫu nhiên). Ảnh đó chụp góc chéo 3/4
        # (không thẳng cạnh như 2 ảnh kia) -- góc quay nghiêng làm méo góc
        # chiếu 2D dù thân người thực tế thẳng, giới hạn cố hữu của cách
        # tính góc từ 1 ảnh đơn (không có depth/3D), không sửa được ở layer
        # rule-based này. Giữ nguyên ảnh đó trong data/pose_rule_samples/
        # làm ví dụ minh hoạ hạn chế này (không âm thầm bỏ) -- score_pose()
        # sẽ báo "issue" cho ảnh đó, biết trước và chấp nhận được.
        AngleRange("hip", 159, 180, "Giữ thân thẳng hàng vai-hông-gót, tránh võng hoặc gù lưng."),
        # Không có rule cho "elbow": ảnh mẫu thật cho thấy lớp "plank" trong
        # dataset gộp cả high plank (tay thẳng, ~170-175 độ) lẫn forearm
        # plank (chống khuỷu tay, ~90 độ) -- 2 biến thể hợp lệ với góc
        # khuỷu tay khác hẳn nhau, 1 ngưỡng duy nhất sẽ chấm sai 1 trong 2.
    ],
    "shoulderstand": [
        AngleRange("hip", 139, 175, "Đẩy hông thẳng lên trên, giữ thân thẳng đứng."),
        AngleRange("knee", 152, 180, "Duỗi thẳng chân lên trời."),
    ],
    "bridge": [
        AngleRange("hip", 124, 176, "Nâng hông lên cao hơn."),
        AngleRange("knee", 46, 88, "Gập gối tự nhiên, giữ bàn chân phẳng trên sàn."),
    ],
}


@dataclass
class FormScore:
    pose: str
    ok: bool
    issues: list[str]


def joint_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle at point b (in degrees), given three (x, y) landmark points."""
    ba = a - b
    bc = c - b
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    return float(np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0))))


def _triplet_angle(triplet_name: str, landmarks: np.ndarray) -> float:
    a_idx, b_idx, c_idx = JOINT_TRIPLETS[triplet_name]
    return joint_angle(landmarks[a_idx], landmarks[b_idx], landmarks[c_idx])


def resolve_joint_angle(joint_name: str, landmarks: np.ndarray) -> float:
    """Map 1 tên khớp trong POSE_RULES sang 1 góc độ thật, tính từ landmarks.

    - "standing_knee"/"bent_knee" (riêng tree): tính cả 2 đầu gối, góc LỚN
      hơn là chân trụ (duỗi thẳng), góc NHỎ hơn là chân co -- không giả định
      trước chân nào, vì người tập có thể đứng trụ chân trái hoặc phải.
    - Khớp đối xứng ("hip"/"knee"/"elbow"): trung bình góc trái + phải.
    """
    if joint_name in ("standing_knee", "bent_knee"):
        left = _triplet_angle("left_knee", landmarks)
        right = _triplet_angle("right_knee", landmarks)
        larger, smaller = max(left, right), min(left, right)
        return larger if joint_name == "standing_knee" else smaller

    if joint_name in SYMMETRIC_JOINTS:
        left = _triplet_angle(f"left_{joint_name}", landmarks)
        right = _triplet_angle(f"right_{joint_name}", landmarks)
        return (left + right) / 2

    raise ValueError(f"Không biết cách tính góc cho khớp {joint_name!r}.")


def score_pose(pose_class: str, landmarks: np.ndarray) -> FormScore:
    """landmarks: (33, 2) array toạ độ pixel (x, y) của MediaPipe Pose landmark
    -- KHÔNG phải toạ độ chuẩn hoá [0,1] MediaPipe trả về mặc định, vì
    joint_angle() không bất biến với scale khác nhau theo trục x/y khi ảnh
    không vuông. Nơi gọi hàm này (app/service.py, scripts/calibrate_pose_rules.py)
    chịu trách nhiệm nhân lại theo (width, height) ảnh gốc trước khi truyền vào.

    pose_class ngoài POSE_RULES (chưa hiệu chỉnh, hoặc lớp lạ) -> coi là
    không có quy tắc để chấm, trả ok=True/issues=[] thay vì crash (T6.5).
    """
    rules = POSE_RULES.get(pose_class)
    if rules is None:
        return FormScore(pose=pose_class, ok=True, issues=[])

    issues: list[str] = []
    for rule in rules:
        angle = resolve_joint_angle(rule.joint, landmarks)
        if not (rule.min_deg <= angle <= rule.max_deg):
            issues.append(rule.tip)

    return FormScore(pose=pose_class, ok=len(issues) == 0, issues=issues)
