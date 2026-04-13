import math

import numpy as np
from typing import Optional

ESSENTIAL_LANDMARKS = [0, 11, 12, 23, 24, 27, 28]


def _round_or_none(value, digits=3):
    if value is None:
        return None
    return round(float(value), digits)


def compute_lighting_score(image: np.ndarray) -> float:
    grayscale = image.mean(axis=2) / 255.0
    mean_brightness = float(np.mean(grayscale))
    return max(0.0, 1.0 - abs(mean_brightness - 0.55) / 0.55)


def summarize_frame_quality(image: np.ndarray, landmarks: Optional[np.ndarray] = None) -> dict:
    lighting_score = compute_lighting_score(image)
    quality = {
        "full_body_visible": False,
        "visibility_score": 0.0,
        "center_offset": None,
        "pose_scale": None,
        "lighting_score": _round_or_none(lighting_score),
    }
    if landmarks is None:
        return quality

    visibilities = landmarks[:, 3]
    essential_vis = visibilities[ESSENTIAL_LANDMARKS]
    visibility_score = float(np.mean(np.clip(essential_vis, 0.0, 1.0)))
    visible_mask = visibilities >= 0.35
    if np.any(visible_mask):
        visible_landmarks = landmarks[visible_mask]
    else:
        visible_landmarks = landmarks

    xs = visible_landmarks[:, 0]
    ys = visible_landmarks[:, 1]
    width = float(max(xs.max() - xs.min(), 1e-6))
    height = float(max(ys.max() - ys.min(), 1e-6))
    pose_scale = max(width, height)
    center_x = float((xs.min() + xs.max()) / 2.0)
    center_y = float((ys.min() + ys.max()) / 2.0)
    center_offset = min(math.sqrt((center_x - 0.5) ** 2 + (center_y - 0.5) ** 2) / 0.707, 1.0)

    quality["visibility_score"] = _round_or_none(visibility_score)
    quality["center_offset"] = _round_or_none(center_offset)
    quality["pose_scale"] = _round_or_none(pose_scale)
    quality["full_body_visible"] = bool(
        visibility_score >= 0.55 and 0.35 <= pose_scale <= 0.95 and center_offset <= 0.35
    )
    return quality


def build_recovery_hints(
    quality: dict,
    pose_detected: bool = True,
    confidence_suppressed: bool = False,
) -> list[str]:
    hints: list[str] = []
    lighting_score = float(quality.get("lighting_score") or 0.0)
    visibility_score = float(quality.get("visibility_score") or 0.0)
    center_offset = quality.get("center_offset")
    pose_scale = quality.get("pose_scale")

    if not pose_detected:
        hints.append("Keep your full body visible from head to feet.")
    if not quality.get("full_body_visible", False) or visibility_score < 0.55:
        hints.append("Keep your full body inside the frame.")
    if center_offset is not None and float(center_offset) > 0.35:
        hints.append("Center your body in front of the camera.")
    if pose_scale is not None and float(pose_scale) > 0.95:
        hints.append("Move farther from the camera.")
    if pose_scale is not None and float(pose_scale) < 0.35:
        hints.append("Move slightly closer to the camera.")
    if lighting_score < 0.4:
        hints.append("Increase lighting or face the light source.")
    if confidence_suppressed:
        hints.append("Hold the pose steady for one second.")

    deduped: list[str] = []
    for hint in hints:
        if hint not in deduped:
            deduped.append(hint)
    return deduped[:3]
