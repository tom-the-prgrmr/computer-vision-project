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
LEFT_ELBOW, RIGHT_ELBOW = 13, 14
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_HIP, RIGHT_HIP = 23, 24
LEFT_KNEE, RIGHT_KNEE = 25, 26
LEFT_ANKLE, RIGHT_ANKLE = 27, 28


class AngleRange(NamedTuple):
    joint: str          # e.g. "left_knee"
    min_deg: float
    max_deg: float
    tip: str             # feedback shown to the user if out of range


# Reference ranges per pose class — TODO: calibrate against a handful of
# "correct form" reference images/videos per class instead of guessing.
POSE_RULES: dict[str, list[AngleRange]] = {
    "tree": [
        AngleRange("standing_knee", 170, 180, "Duỗi thẳng chân trụ hơn."),
        AngleRange("bent_knee", 20, 90, "Mở đầu gối chân co ra ngoài nhiều hơn."),
    ],
    "warrior2": [
        AngleRange("front_knee", 80, 100, "Hạ thấp gối trước xuống góc 90 độ."),
        AngleRange("back_knee", 160, 180, "Duỗi thẳng chân sau."),
    ],
    # ... thêm các tư thế còn lại sau khi chốt danh sách lớp v1/v2
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


def score_pose(pose_class: str, landmarks: np.ndarray) -> FormScore:
    """landmarks: (33, 2) array of MediaPipe Pose landmark (x, y) in pixels.

    TODO: implement per-joint angle extraction for each pose in POSE_RULES,
    compare against AngleRange, collect issues.
    """
    raise NotImplementedError("Implement once POSE_RULES is calibrated for the chosen classes.")
