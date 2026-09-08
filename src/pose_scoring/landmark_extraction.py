"""MediaPipe Pose landmark extraction -- shared by scripts/calibrate_pose_rules.py
now, and by app/service.py's `_extract_landmarks()` later (Giai đoạn 7).
Kept separate from angle_rules.py so that module stays pure geometry/rules
(no MediaPipe model I/O), easier to unit-test in isolation.
"""

import cv2
import mediapipe as mp
import numpy as np

_mp_pose = mp.solutions.pose


def new_pose_model():
    """1 instance MediaPipe Pose, tái sử dụng qua nhiều lần extract_landmarks_px()
    thay vì khởi tạo lại mỗi ảnh (tốn thời gian load model). Caller chịu
    trách nhiệm gọi `.close()` khi xong (hoặc dùng `with`) -- app/service.py
    sẽ giữ 1 instance suốt vòng đời app, giống cách nó load model YOLO 1 lần
    lúc startup (xem CLAUDE.md mục Pipeline wiring)."""
    return _mp_pose.Pose(static_image_mode=True, model_complexity=1)


def extract_landmarks_px(image_bgr: np.ndarray, pose) -> np.ndarray | None:
    """Chạy MediaPipe Pose (`pose`, từ new_pose_model()) trên 1 ảnh (OpenCV
    BGR array), trả landmarks (33, 2) toạ độ PIXEL thật -- nhân lại theo
    (width, height) ảnh gốc, vì MediaPipe mặc định trả toạ độ chuẩn hoá
    [0,1] (score_pose() cần pixel, xem docstring của nó). Trả None nếu
    không detect được người nào.
    """
    height, width = image_bgr.shape[:2]
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    result = pose.process(image_rgb)
    if result.pose_landmarks is None:
        return None
    return np.array(
        [[lm.x * width, lm.y * height] for lm in result.pose_landmarks.landmark],
        dtype=np.float32,
    )
