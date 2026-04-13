import json
import os
from typing import Optional
import time

from models.pose_correction import get_rules_for_pose

PROFILE_VERSION = 1
CALIBRATION_SAMPLES_REQUIRED = 10
CALIBRATION_STEPS = {
    "neutral": {
        "label": "Neutral stance",
        "pose_name": None,
    },
    "chair": {
        "label": "Chair pose",
        "pose_name": "chair pose",
    },
    "warrior_ii": {
        "label": "Warrior II pose",
        "pose_name": "warrior ii pose",
    },
}


def safe_user_id(user_id: str) -> str:
    safe = "".join(ch if (ch.isalnum() or ch in ("-", "_", ".")) else "_" for ch in user_id)
    return safe or "anonymous"


def profile_path(profile_dir: str, user_id: str) -> str:
    return os.path.join(profile_dir, f"{safe_user_id(user_id)}.json")


def empty_profile(user_id: str) -> dict:
    now = time.time()
    return {
        "version": PROFILE_VERSION,
        "user_id": user_id,
        "created_at": now,
        "updated_at": now,
        "calibrated_at": None,
        "completed_steps": [],
        "global_angle_offsets": {},
        "per_pose_thresholds": {},
        "calibration": {
            "required_samples": CALIBRATION_SAMPLES_REQUIRED,
            "steps": {
                step_id: {
                    "label": meta["label"],
                    "pose_name": meta["pose_name"],
                    "sample_count": 0,
                    "avg_angles": {},
                    "last_quality": None,
                }
                for step_id, meta in CALIBRATION_STEPS.items()
            },
        },
    }


def load_profile(profile_dir: str, user_id: str, create_if_missing: bool = False) -> Optional[dict]:
    path = profile_path(profile_dir, user_id)
    if not os.path.exists(path):
        if create_if_missing:
            return empty_profile(user_id)
        return None
    with open(path, "r", encoding="utf-8") as f:
        profile = json.load(f)
    profile.setdefault("version", PROFILE_VERSION)
    profile.setdefault("user_id", user_id)
    profile.setdefault("completed_steps", [])
    profile.setdefault("global_angle_offsets", {})
    profile.setdefault("per_pose_thresholds", {})
    calibration = profile.setdefault("calibration", {})
    calibration.setdefault("required_samples", CALIBRATION_SAMPLES_REQUIRED)
    steps = calibration.setdefault("steps", {})
    for step_id, meta in CALIBRATION_STEPS.items():
        steps.setdefault(
            step_id,
            {
                "label": meta["label"],
                "pose_name": meta["pose_name"],
                "sample_count": 0,
                "avg_angles": {},
                "last_quality": None,
            },
        )
    return profile


def save_profile(profile_dir: str, user_id: str, profile: dict) -> str:
    os.makedirs(profile_dir, exist_ok=True)
    profile["updated_at"] = time.time()
    path = profile_path(profile_dir, user_id)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
    os.replace(tmp, path)
    return path


def _step_state(profile: dict, step_id: str) -> dict:
    steps = profile.setdefault("calibration", {}).setdefault("steps", {})
    if step_id not in CALIBRATION_STEPS:
        raise ValueError(f"Unsupported calibration step: {step_id}")
    return steps[step_id]


def update_calibration_step(profile: dict, step_id: str, angles: dict, quality: dict) -> dict:
    step = _step_state(profile, step_id)
    count = int(step.get("sample_count", 0))
    avg_angles = step.setdefault("avg_angles", {})

    for angle_key, value in angles.items():
        prev = float(avg_angles.get(angle_key, 0.0))
        avg_angles[angle_key] = ((prev * count) + float(value)) / (count + 1)

    step["sample_count"] = count + 1
    step["last_quality"] = quality

    required = int(profile["calibration"].get("required_samples", CALIBRATION_SAMPLES_REQUIRED))
    if step_id not in profile["completed_steps"] and step["sample_count"] >= required:
        profile["completed_steps"].append(step_id)

    return step


def finalize_profile(profile: dict) -> dict:
    offsets: dict[str, list[float]] = {}
    for step_id in profile.get("completed_steps", []):
        step = _step_state(profile, step_id)
        pose_name = step.get("pose_name")
        if not pose_name:
            continue
        avg_angles = step.get("avg_angles", {})
        for rule in get_rules_for_pose(pose_name):
            angle_key = rule["angle_key"]
            if angle_key not in avg_angles:
                continue
            center = (float(rule["min"]) + float(rule["max"])) / 2.0
            offsets.setdefault(angle_key, []).append(float(avg_angles[angle_key]) - center)

    profile["global_angle_offsets"] = {
        angle_key: round(sum(values) / len(values), 2)
        for angle_key, values in offsets.items()
        if values
    }
    if profile.get("completed_steps"):
        profile["calibrated_at"] = time.time()
    return profile


def profile_summary(profile: Optional[dict]) -> Optional[dict]:
    if profile is None:
        return None
    calibration = profile.get("calibration", {})
    steps = calibration.get("steps", {})
    return {
        "version": profile.get("version", PROFILE_VERSION),
        "calibrated_at": profile.get("calibrated_at"),
        "completed_steps": profile.get("completed_steps", []),
        "global_angle_offsets": profile.get("global_angle_offsets", {}),
        "per_pose_thresholds": profile.get("per_pose_thresholds", {}),
        "required_samples": calibration.get("required_samples", CALIBRATION_SAMPLES_REQUIRED),
        "step_progress": {
            step_id: {
                "label": meta["label"],
                "sample_count": int(steps.get(step_id, {}).get("sample_count", 0)),
                "pose_name": meta["pose_name"],
            }
            for step_id, meta in CALIBRATION_STEPS.items()
        },
    }
