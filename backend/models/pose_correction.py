import re
from typing import Optional

MAX_ABS_ANGLE_OFFSET = 20.0


def normalize_pose_name(pose_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", pose_name.lower()).strip()


def _rule(angle_key, min_v, max_v, joint, low_msg, high_msg, priority=1):
    return {
        "angle_key": angle_key,
        "min": min_v,
        "max": max_v,
        "joint": joint,
        "low_msg": low_msg,
        "high_msg": high_msg,
        "priority": priority,
    }


# Pose-aware rules for common coaching poses.
# Ranges are intentionally tolerant for real-time webcam coaching.
POSE_RULES = {
    "downward facing dog": [
        _rule("left_elbow", 160, 195, "left_elbow", "Straighten your left arm.", "Relax your left elbow slightly.", 1),
        _rule("right_elbow", 160, 195, "right_elbow", "Straighten your right arm.", "Relax your right elbow slightly.", 1),
        _rule("left_hip", 70, 120, "left_hip", "Lift your hips higher.", "Lower your hips slightly.", 2),
        _rule("right_hip", 70, 120, "right_hip", "Lift your hips higher.", "Lower your hips slightly.", 2),
    ],
    "chair pose": [
        _rule("left_knee", 70, 120, "left_knee", "Bend your left knee deeper.", "Do not squat too low with the left knee.", 1),
        _rule("right_knee", 70, 120, "right_knee", "Bend your right knee deeper.", "Do not squat too low with the right knee.", 1),
        _rule("left_shoulder", 140, 190, "left_shoulder", "Raise your left arm overhead.", "Soften your left shoulder slightly.", 2),
        _rule("right_shoulder", 140, 190, "right_shoulder", "Raise your right arm overhead.", "Soften your right shoulder slightly.", 2),
    ],
    "tree pose": [
        _rule("left_hip", 120, 180, "left_hip", "Open your left hip more.", "Square your left hip slightly.", 1),
        _rule("right_hip", 120, 180, "right_hip", "Open your right hip more.", "Square your right hip slightly.", 1),
    ],
    "warrior ii pose": [
        _rule("left_knee", 80, 130, "left_knee", "Bend your left front knee.", "Do not over-bend your left knee.", 1),
        _rule("right_knee", 145, 195, "right_knee", "Straighten your right leg.", "Soften your right back knee slightly.", 1),
        _rule("left_shoulder", 70, 130, "left_shoulder", "Extend your left arm parallel to the floor.", "Lower your left arm slightly.", 2),
        _rule("right_shoulder", 70, 130, "right_shoulder", "Extend your right arm parallel to the floor.", "Lower your right arm slightly.", 2),
    ],
    "warrior i pose": [
        _rule("left_knee", 85, 140, "left_knee", "Bend your left front knee.", "Ease your left knee bend slightly.", 1),
        _rule("right_knee", 145, 195, "right_knee", "Straighten your right back leg.", "Soften your right back knee slightly.", 1),
        _rule("left_shoulder", 140, 195, "left_shoulder", "Reach your left arm overhead.", "Relax your left shoulder slightly.", 2),
        _rule("right_shoulder", 140, 195, "right_shoulder", "Reach your right arm overhead.", "Relax your right shoulder slightly.", 2),
    ],
    "plank pose": [
        _rule("left_elbow", 160, 195, "left_elbow", "Straighten your left arm.", "Unlock your left elbow slightly.", 1),
        _rule("right_elbow", 160, 195, "right_elbow", "Straighten your right arm.", "Unlock your right elbow slightly.", 1),
        _rule("left_hip", 145, 195, "left_hip", "Lift your hips to align your body.", "Lower your hips to align your body.", 2),
        _rule("right_hip", 145, 195, "right_hip", "Lift your hips to align your body.", "Lower your hips to align your body.", 2),
    ],
    "cobra pose": [
        _rule("left_elbow", 120, 180, "left_elbow", "Press more through your left arm.", "Soften your left elbow slightly.", 1),
        _rule("right_elbow", 120, 180, "right_elbow", "Press more through your right arm.", "Soften your right elbow slightly.", 1),
        _rule("left_shoulder", 90, 170, "left_shoulder", "Open your chest more.", "Relax your left shoulder down.", 2),
        _rule("right_shoulder", 90, 170, "right_shoulder", "Open your chest more.", "Relax your right shoulder down.", 2),
    ],
    "warrior iii pose": [
        _rule("left_hip", 145, 195, "left_hip", "Lift and lengthen your left side body.", "Lower your left side body slightly.", 1),
        _rule("right_hip", 145, 195, "right_hip", "Lift and lengthen your right side body.", "Lower your right side body slightly.", 1),
        _rule("left_knee", 150, 195, "left_knee", "Straighten your left standing leg.", "Soften your left standing knee slightly.", 2),
        _rule("right_knee", 150, 195, "right_knee", "Straighten your right lifted leg.", "Soften your right lifted knee slightly.", 2),
    ],
    "triangle pose": [
        _rule("left_knee", 150, 195, "left_knee", "Straighten your left leg.", "Soften your left knee slightly.", 1),
        _rule("right_knee", 150, 195, "right_knee", "Straighten your right leg.", "Soften your right knee slightly.", 1),
        _rule("left_shoulder", 140, 195, "left_shoulder", "Reach your left arm up.", "Relax your left shoulder slightly.", 2),
        _rule("right_shoulder", 140, 195, "right_shoulder", "Reach your right arm up.", "Relax your right shoulder slightly.", 2),
    ],
    "extended revolved triangle pose": [
        _rule("left_knee", 150, 195, "left_knee", "Straighten your left leg.", "Soften your left knee slightly.", 1),
        _rule("right_knee", 150, 195, "right_knee", "Straighten your right leg.", "Soften your right knee slightly.", 1),
    ],
    "extended revolved side angle pose": [
        _rule("left_knee", 80, 130, "left_knee", "Bend your left front knee more.", "Do not over-bend your left knee.", 1),
        _rule("right_knee", 140, 195, "right_knee", "Straighten your right back leg.", "Soften your right back knee slightly.", 1),
    ],
    "reverse warrior pose": [
        _rule("left_knee", 80, 130, "left_knee", "Bend your left front knee.", "Do not over-bend your left knee.", 1),
        _rule("right_knee", 140, 195, "right_knee", "Straighten your right back leg.", "Soften your right back knee slightly.", 1),
        _rule("left_shoulder", 130, 195, "left_shoulder", "Reach your left arm overhead.", "Relax your left shoulder slightly.", 2),
    ],
    "bridge pose": [
        _rule("left_knee", 70, 120, "left_knee", "Bend your left knee and stack it over ankle.", "Move your left foot slightly forward.", 1),
        _rule("right_knee", 70, 120, "right_knee", "Bend your right knee and stack it over ankle.", "Move your right foot slightly forward.", 1),
        _rule("left_hip", 145, 195, "left_hip", "Lift your hips higher.", "Lower your hips slightly.", 2),
        _rule("right_hip", 145, 195, "right_hip", "Lift your hips higher.", "Lower your hips slightly.", 2),
    ],
    "bow pose": [
        _rule("left_knee", 40, 110, "left_knee", "Bend your left knee deeper.", "Do not close your left knee too much.", 1),
        _rule("right_knee", 40, 110, "right_knee", "Bend your right knee deeper.", "Do not close your right knee too much.", 1),
        _rule("left_shoulder", 110, 195, "left_shoulder", "Lift your chest more.", "Relax your left shoulder slightly.", 2),
        _rule("right_shoulder", 110, 195, "right_shoulder", "Lift your chest more.", "Relax your right shoulder slightly.", 2),
    ],
    "camel pose": [
        _rule("left_hip", 120, 185, "left_hip", "Press your hips forward.", "Ease your backbend slightly.", 1),
        _rule("right_hip", 120, 185, "right_hip", "Press your hips forward.", "Ease your backbend slightly.", 1),
        _rule("left_shoulder", 100, 190, "left_shoulder", "Open your chest upward.", "Relax your left shoulder slightly.", 2),
        _rule("right_shoulder", 100, 190, "right_shoulder", "Open your chest upward.", "Relax your right shoulder slightly.", 2),
    ],
    "boat pose": [
        _rule("left_knee", 140, 195, "left_knee", "Straighten your left leg more.", "Soften your left knee slightly.", 1),
        _rule("right_knee", 140, 195, "right_knee", "Straighten your right leg more.", "Soften your right knee slightly.", 1),
        _rule("left_hip", 45, 105, "left_hip", "Lift your chest and engage core.", "Lean back slightly less.", 2),
        _rule("right_hip", 45, 105, "right_hip", "Lift your chest and engage core.", "Lean back slightly less.", 2),
    ],
    "upward plank pose": [
        _rule("left_elbow", 160, 195, "left_elbow", "Straighten your left arm.", "Unlock your left elbow slightly.", 1),
        _rule("right_elbow", 160, 195, "right_elbow", "Straighten your right arm.", "Unlock your right elbow slightly.", 1),
        _rule("left_hip", 145, 195, "left_hip", "Lift your hips higher.", "Lower your hips slightly.", 2),
        _rule("right_hip", 145, 195, "right_hip", "Lift your hips higher.", "Lower your hips slightly.", 2),
    ],
    "side plank pose": [
        _rule("left_elbow", 160, 195, "left_elbow", "Press through your left supporting arm.", "Soften your left elbow slightly.", 1),
        _rule("right_elbow", 160, 195, "right_elbow", "Press through your right supporting arm.", "Soften your right elbow slightly.", 1),
        _rule("left_hip", 145, 195, "left_hip", "Lift your hips to keep a straight line.", "Lower your hips slightly.", 2),
        _rule("right_hip", 145, 195, "right_hip", "Lift your hips to keep a straight line.", "Lower your hips slightly.", 2),
    ],
    "dolphin plank pose": [
        _rule("left_elbow", 70, 130, "left_elbow", "Stack your left shoulder over elbow.", "Shift your left shoulder slightly back.", 1),
        _rule("right_elbow", 70, 130, "right_elbow", "Stack your right shoulder over elbow.", "Shift your right shoulder slightly back.", 1),
        _rule("left_hip", 145, 195, "left_hip", "Lift hips into one straight line.", "Lower your hips slightly.", 2),
        _rule("right_hip", 145, 195, "right_hip", "Lift hips into one straight line.", "Lower your hips slightly.", 2),
    ],
    "dolphin pose": [
        _rule("left_elbow", 70, 130, "left_elbow", "Keep left forearm grounded.", "Shift your left shoulder back slightly.", 1),
        _rule("right_elbow", 70, 130, "right_elbow", "Keep right forearm grounded.", "Shift your right shoulder back slightly.", 1),
        _rule("left_hip", 80, 130, "left_hip", "Lift your hips higher.", "Lower your hips slightly.", 2),
        _rule("right_hip", 80, 130, "right_hip", "Lift your hips higher.", "Lower your hips slightly.", 2),
    ],
    "four limbed staff pose": [
        _rule("left_elbow", 70, 120, "left_elbow", "Bend your left elbow to ninety degrees.", "Do not collapse your left elbow too far.", 1),
        _rule("right_elbow", 70, 120, "right_elbow", "Bend your right elbow to ninety degrees.", "Do not collapse your right elbow too far.", 1),
        _rule("left_hip", 150, 195, "left_hip", "Keep hips aligned with shoulders.", "Lower hips slightly.", 2),
        _rule("right_hip", 150, 195, "right_hip", "Keep hips aligned with shoulders.", "Lower hips slightly.", 2),
    ],
    "child pose": [
        _rule("left_hip", 40, 115, "left_hip", "Sit your hips back toward heels.", "Ease your left hip flexion slightly.", 1),
        _rule("right_hip", 40, 115, "right_hip", "Sit your hips back toward heels.", "Ease your right hip flexion slightly.", 1),
    ],
}


FALLBACK_RULES = [
    _rule("left_knee", 150, 195, "left_knee", "Straighten your left knee.", "Soften your left knee slightly.", 1),
    _rule("right_knee", 150, 195, "right_knee", "Straighten your right knee.", "Soften your right knee slightly.", 1),
    _rule("left_elbow", 160, 195, "left_elbow", "Extend your left arm.", "Relax your left elbow slightly.", 2),
    _rule("right_elbow", 160, 195, "right_elbow", "Extend your right arm.", "Relax your right elbow slightly.", 2),
]


def get_rules_for_pose(pose_name: str):
    normalized = normalize_pose_name(pose_name)
    for key, rules in POSE_RULES.items():
        if key in normalized:
            return rules
    return FALLBACK_RULES


def _severity(value, low, high):
    center = (low + high) / 2.0
    radius = max((high - low) / 2.0, 1e-6)
    return min(abs(value - center) / radius, 2.0)


def _clamped_angle_offset(angle_offsets: Optional[dict], angle_key: str) -> float:
    if not angle_offsets:
        return 0.0
    try:
        offset = float(angle_offsets.get(angle_key, 0.0))
    except (TypeError, ValueError):
        return 0.0
    return max(-MAX_ABS_ANGLE_OFFSET, min(MAX_ABS_ANGLE_OFFSET, offset))


def build_pose_issues(pose_name: str, angles: dict, angle_offsets: Optional[dict] = None):
    issues = []
    for rule in get_rules_for_pose(pose_name):
        angle_key = rule["angle_key"]
        if angle_key not in angles:
            continue
        value = float(angles[angle_key])
        offset = _clamped_angle_offset(angle_offsets, angle_key)
        low = rule["min"] + offset
        high = rule["max"] + offset
        if low <= value <= high:
            continue
        direction = "increase" if value < low else "decrease"
        target = f"{int(round(low))}-{int(round(high))}"
        message = rule["low_msg"] if value < low else rule["high_msg"]
        issues.append(
            {
                "joint": rule["joint"],
                "angle_key": angle_key,
                "current_angle": round(value, 1),
                "target_range": target,
                "direction_to_fix": direction,
                "severity": round(_severity(value, low, high), 3),
                "priority": rule["priority"],
                "message": message,
                "personalized_offset": round(offset, 2),
            }
        )
    issues.sort(key=lambda x: (-x["severity"], x["priority"], x["joint"]))
    return issues
