"""T6.4 -- test thủ công `score_pose()`, chạy local (không cần Colab/GPU).

Hai phần:
1. Ảnh mẫu "form đúng" thật (data/pose_rule_samples/) -- kỳ vọng đa số
   ok=True. Không bắt buộc 100% (ngưỡng có dung sai, ảnh thật luôn hơi
   lệch) -- xem docs/specs/g6-form-scoring.md.
2. Landmark tổng hợp (synthetic), CHỦ ĐỘNG lệch 1 góc ra ngoài ngưỡng --
   kỳ vọng ok=False với đúng tip. Đây là test logic (unit-test kiểu
   synthetic edge-case), KHÔNG PHẢI benchmark trên ảnh sai thật (dataset
   không có nguồn ảnh "form sai" gắn nhãn sẵn).

Usage (từ repo root): python -m scripts.manual_test_score_pose
"""

from pathlib import Path

import cv2
import numpy as np

from src.pose_scoring.angle_rules import JOINT_TRIPLETS, POSE_RULES, score_pose
from src.pose_scoring.landmark_extraction import extract_landmarks_px, new_pose_model

SAMPLES_ROOT = Path("data/pose_rule_samples")


def set_angle(landmarks: np.ndarray, triplet_name: str, angle_deg: float) -> None:
    """Ghi đè 3 điểm landmark của `triplet_name` (từ JOINT_TRIPLETS) để góc
    tại đỉnh giữa đúng bằng `angle_deg` -- dựng hình học trực tiếp, không
    cần ảnh thật, cho phép test chính xác 1 giá trị góc cụ thể."""
    a_idx, b_idx, c_idx = JOINT_TRIPLETS[triplet_name]
    theta = np.radians(angle_deg)
    landmarks[b_idx] = [0.0, 0.0]
    landmarks[a_idx] = [0.0, 1.0]
    landmarks[c_idx] = [np.sin(theta), np.cos(theta)]


def part1_real_images() -> None:
    print("=== Phần 1: ảnh mẫu thật (form đúng) ===")
    n_ok = 0
    n_total = 0
    with new_pose_model() as pose:
        for pose_class in POSE_RULES:
            class_dir = SAMPLES_ROOT / pose_class
            for image_path in sorted(class_dir.glob("*.jpg")) + sorted(class_dir.glob("*.png")):
                image_bgr = cv2.imread(str(image_path))
                image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB) if image_bgr is not None else None
                landmarks_px = extract_landmarks_px(image_rgb, pose) if image_rgb is not None else None
                if landmarks_px is None:
                    print(f"  {pose_class}/{image_path.name}: KHÔNG detect được người -- bỏ qua")
                    continue
                result = score_pose(pose_class, landmarks_px)
                n_total += 1
                n_ok += result.ok
                status = "OK  " if result.ok else "ISSUES"
                print(f"  {status} {pose_class}/{image_path.name}: {result.issues if result.issues else '(không có issue)'}")
    print(f"-- {n_ok}/{n_total} ảnh mẫu được chấm ok=True --\n")


def part2_synthetic_sai() -> None:
    print("=== Phần 2: landmark tổng hợp, chủ động lệch góc (kỳ vọng ok=False) ===")
    n_pass = 0
    n_total = 0
    for pose_class, rules in POSE_RULES.items():
        rule = rules[0]  # test bằng rule đầu tiên của mỗi lớp
        landmarks = np.zeros((33, 2), dtype=np.float32)
        out_of_range_angle = max(0.0, rule.min_deg - 20.0)  # chắc chắn dưới min_deg

        if rule.joint in ("standing_knee", "bent_knee"):
            # Cả 2 chân cùng ở out_of_range_angle -> góc lớn hơn (standing)
            # vẫn có thể hợp lệ tình cờ; ép cả 2 cùng thấp để chắc chắn cả
            # standing_knee lẫn bent_knee đều lệch theo hướng cần test.
            set_angle(landmarks, "left_knee", out_of_range_angle)
            set_angle(landmarks, "right_knee", out_of_range_angle)
        else:
            set_angle(landmarks, f"left_{rule.joint}", out_of_range_angle)
            set_angle(landmarks, f"right_{rule.joint}", out_of_range_angle)

        result = score_pose(pose_class, landmarks)
        n_total += 1
        expected_fail = rule.tip in result.issues and not result.ok
        n_pass += expected_fail
        status = "PASS" if expected_fail else "FAIL"
        print(
            f"  [{status}] {pose_class}: ép '{rule.joint}'={out_of_range_angle:.0f}° "
            f"(ngoài [{rule.min_deg},{rule.max_deg}]) -> ok={result.ok}, issues={result.issues}"
        )
    print(f"-- {n_pass}/{n_total} case synthetic phát hiện đúng lỗi kỳ vọng --")


if __name__ == "__main__":
    part1_real_images()
    part2_synthetic_sai()
