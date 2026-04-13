# models/pose_feedback.py

def generate_feedback(predicted_pose, angles):
    """
    predicted_pose: str
    angles: dict returned by extract_joint_angles
    returns: list of feedback strings
    """

    feedback = []

    # -------------------------
    # Generic yoga rules
    # -------------------------
    if angles["left_knee"] < 150:
        feedback.append("Straighten your left knee")

    if angles["right_knee"] < 150:
        feedback.append("Straighten your right knee")

    if angles["left_elbow"] < 160:
        feedback.append("Extend your left arm")

    if angles["right_elbow"] < 160:
        feedback.append("Extend your right arm")

    if angles["hip"] < 140:
        feedback.append("Open your hips more")

    # -------------------------
    # Pose-aware placeholder (future-ready)
    # -------------------------
    # Example:
    # if predicted_pose == "Warrior II" and angles["left_knee"] < 120:
    #     feedback.append("Bend your front knee deeper for Warrior II")

    if not feedback:
        feedback.append("Great posture! Hold steady 🧘‍♀️")

    return feedback
