# models/pose_angles.py
import numpy as np

# -------------------------------------------------
# Utility to compute angle between 3 joints
# -------------------------------------------------
def compute_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))
    return angle


# -------------------------------------------------
# Extract important yoga-related joint angles
# -------------------------------------------------
def extract_joint_angles(landmarks):
    """
    landmarks: np.ndarray of shape (33, 4)
    returns: dict of joint angles
    """
    angles = {}

    # Knees
    angles["left_knee"] = compute_angle(
        landmarks[23][:3], landmarks[25][:3], landmarks[27][:3]
    )
    angles["right_knee"] = compute_angle(
        landmarks[24][:3], landmarks[26][:3], landmarks[28][:3]
    )

    # Elbows
    angles["left_elbow"] = compute_angle(
        landmarks[11][:3], landmarks[13][:3], landmarks[15][:3]
    )
    angles["right_elbow"] = compute_angle(
        landmarks[12][:3], landmarks[14][:3], landmarks[16][:3]
    )

    # Hip openness
    angles["hip"] = compute_angle(
        landmarks[11][:3], landmarks[23][:3], landmarks[25][:3]
    )

    return angles
