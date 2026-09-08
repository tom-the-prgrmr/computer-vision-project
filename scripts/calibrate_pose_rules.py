"""Hiệu chỉnh ngưỡng góc trong `src/pose_scoring/angle_rules.py::POSE_RULES`.

Chạy 1 lần (không phải notebook -- không cần Colab/GPU, MediaPipe CPU đủ
nhanh cho vài chục ảnh): với mỗi ảnh mẫu "form đúng" trong
`data/pose_rule_samples/<lop>/`, chạy MediaPipe Pose, in góc thật của từng
khớp liên quan tới lớp đó. Dùng số in ra đây để chốt `min_deg`/`max_deg`
trong POSE_RULES (cộng biên độ dung sai, không chốt đúng y hệt số đo được
-- ảnh khác sẽ lệch chút). Xem docs/specs/g6-form-scoring.md (T6.2).

Usage (từ repo root -- chạy dạng module để `src` import được):
    python -m scripts.calibrate_pose_rules
"""

from pathlib import Path

import cv2

from src.pose_scoring.angle_rules import POSE_RULES, resolve_joint_angle
from src.pose_scoring.landmark_extraction import extract_landmarks_px, new_pose_model

SAMPLES_ROOT = Path("data/pose_rule_samples")

# Khớp cần in cho mỗi lớp -- lấy trực tiếp từ POSE_RULES hiện có, để calibrate
# luôn khớp với đúng những gì score_pose() sẽ dùng.
JOINTS_PER_CLASS = {cls: [rule.joint for rule in rules] for cls, rules in POSE_RULES.items()}


def main() -> None:
    with new_pose_model() as pose:
        for pose_class, joints in JOINTS_PER_CLASS.items():
            print(f"\n=== {pose_class} ===")
            class_dir = SAMPLES_ROOT / pose_class
            image_paths = sorted(class_dir.glob("*.jpg")) + sorted(class_dir.glob("*.png"))
            if not image_paths:
                print(f"  (không có ảnh mẫu trong {class_dir})")
                continue

            angles_by_joint: dict[str, list[float]] = {j: [] for j in joints}
            for image_path in image_paths:
                image_bgr = cv2.imread(str(image_path))
                landmarks_px = extract_landmarks_px(image_bgr, pose) if image_bgr is not None else None
                if landmarks_px is None:
                    print(f"  {image_path.name}: KHÔNG detect được người -- bỏ qua")
                    continue
                readings = []
                for joint in joints:
                    angle = resolve_joint_angle(joint, landmarks_px)
                    angles_by_joint[joint].append(angle)
                    readings.append(f"{joint}={angle:.1f}")
                print(f"  {image_path.name}: {', '.join(readings)}")

            print("  -- tổng hợp --")
            for joint, values in angles_by_joint.items():
                if values:
                    print(f"  {joint}: min={min(values):.1f} max={max(values):.1f} mean={sum(values) / len(values):.1f}")
                else:
                    print(f"  {joint}: không có số đo (không ảnh nào detect được)")


if __name__ == "__main__":
    main()
