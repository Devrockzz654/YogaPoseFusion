# ============================================================
# YogaPoseFusion v4 — Ensemble Inference Backend (FastAPI + PyTorch + Spectral Features)
# ============================================================

import os
import io
import json
import base64
import time
import hashlib
from collections import deque, Counter
from typing import Optional
import numpy as np
import torch
import torch.nn as nn
import mediapipe as mp
from fastapi import FastAPI, UploadFile, File, WebSocket, Form, Body, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image
import joblib
try:
    from openai import OpenAI
except Exception:
    OpenAI = None
from models.pose_graph_spectral import build_pose_graph
from models.pose_correction import build_pose_issues, normalize_pose_name
from models.frame_quality import build_recovery_hints, summarize_frame_quality
from models.personalization import (
    CALIBRATION_SAMPLES_REQUIRED,
    CALIBRATION_STEPS,
    finalize_profile,
    load_profile,
    profile_summary,
    save_profile,
    update_calibration_step,
)
from models.recommendations import (
    build_recommendation_plan,
    build_target_pose_guidance,
    pose_catalog,
    reference_image_path_for_pose,
    resolve_pose_by_slug,
)


# ---------------- CONFIG ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
PROFILE_DIR = os.path.join(BASE_DIR, "data", "profiles")
LOG_DIR = os.path.join(BASE_DIR, "logs", "sessions")
TTS_CACHE_DIR = os.path.join(BASE_DIR, "data", "tts_cache")

POSE_MAPPING_PATH = os.path.join(DATA_DIR, "idx_to_pose.json")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")

MODEL_PATHS = [
    os.path.join(MODEL_DIR, f"pose_classifier_v4_fold{i}.pt")
    for i in range(1, 6)
]

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else
                      "cuda" if torch.cuda.is_available() else "cpu")

print(f"✅ Using device: {DEVICE}")

# ---------------- LOAD LABEL MAPPING ----------------
if not os.path.exists(POSE_MAPPING_PATH):
    raise FileNotFoundError(f"❌ idx_to_pose.json not found at {POSE_MAPPING_PATH}")

with open(POSE_MAPPING_PATH, "r") as f:
    idx_to_pose = json.load(f)

num_classes = len(idx_to_pose)
input_dim = 33 * 4 + 5  # 33 joints × (x, y, z, visibility) + 5 spectral
CONFIDENCE_GATE = 0.55
TRANSIENT_ALERT_S = 1.0
SUMMARY_PERSIST_EVERY_FRAMES = 30
TTS_DEFAULT_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts-2025-12-15")
TTS_DEFAULT_VOICE = os.getenv("OPENAI_TTS_VOICE", "marin")
TTS_DEFAULT_FORMAT = os.getenv("OPENAI_TTS_FORMAT", "mp3")
TTS_TEXT_LIMIT = 4096
_tts_client = None

# ============================================================
# MODEL ARCHITECTURE — Must Match Training (v4)
# ============================================================
class ResidualBlock(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.layer = nn.Sequential(
            nn.Linear(dim, dim),
            nn.BatchNorm1d(dim),
            nn.ReLU(),
            nn.Dropout(0.3)
        )

    def forward(self, x):
        return x + self.layer(x)


class YogaPoseFusionNet(nn.Module):
    def __init__(self, input_dim, num_classes):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(),
            nn.Dropout(0.4),
            ResidualBlock(1024),

            nn.Linear(1024, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.4),
            ResidualBlock(512),

            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        return self.net(x)


# ============================================================
# LOAD ALL MODELS (Ensemble)
# ============================================================
models = []
for path in MODEL_PATHS:
    if os.path.exists(path):
        model = YogaPoseFusionNet(input_dim, num_classes)
        model.load_state_dict(torch.load(path, map_location=DEVICE))
        model.to(DEVICE)
        model.eval()
        models.append(model)
        print(f"✅ Loaded: {os.path.basename(path)}")
    else:
        print(f"⚠️ Model file missing: {path}")

if not models:
    raise RuntimeError("❌ No ensemble models found. Please check MODEL_PATHS.")

print(f"✅ Ensemble initialized with {len(models)} models.")

# ============================================================
# LOAD SCALER
# ============================================================
if not os.path.exists(SCALER_PATH):
    raise FileNotFoundError(f"❌ Scaler file not found at {SCALER_PATH}")
scaler = joblib.load(SCALER_PATH)

# ============================================================
# MEDIAPIPE POSE INITIALIZATION
# ============================================================
try:
    mp_pose = mp.solutions.pose
except AttributeError:
    # Some Linux deploy environments expose the legacy solutions API only via
    # the explicit Python package path.
    from mediapipe.python.solutions import pose as mp_pose

pose_detector = mp_pose.Pose(static_image_mode=True, model_complexity=2)
pose_detector_video = mp_pose.Pose(static_image_mode=False, model_complexity=2, min_detection_confidence=0.5)

# ============================================================
# REAL-TIME HELPERS (INLINE) — No external feedback/angles files
# ============================================================
def compute_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))


def extract_angles(landmarks):
    # landmarks: (33,4)
    angles = {}
    angles["left_knee"] = compute_angle(landmarks[23][:3], landmarks[25][:3], landmarks[27][:3])
    angles["right_knee"] = compute_angle(landmarks[24][:3], landmarks[26][:3], landmarks[28][:3])
    angles["left_elbow"] = compute_angle(landmarks[11][:3], landmarks[13][:3], landmarks[15][:3])
    angles["right_elbow"] = compute_angle(landmarks[12][:3], landmarks[14][:3], landmarks[16][:3])
    angles["left_hip"] = compute_angle(landmarks[11][:3], landmarks[23][:3], landmarks[25][:3])
    angles["right_hip"] = compute_angle(landmarks[12][:3], landmarks[24][:3], landmarks[26][:3])
    angles["left_shoulder"] = compute_angle(landmarks[23][:3], landmarks[11][:3], landmarks[13][:3])
    angles["right_shoulder"] = compute_angle(landmarks[24][:3], landmarks[12][:3], landmarks[14][:3])
    return angles


def generate_feedback(angles):
    feedback = []
    if angles["left_knee"] < 150:
        feedback.append("Straighten left knee")
    if angles["right_knee"] < 150:
        feedback.append("Straighten right knee")
    if angles["left_elbow"] < 160:
        feedback.append("Extend left arm")
    if angles["right_elbow"] < 160:
        feedback.append("Extend right arm")
    if angles["left_hip"] < 140 and angles["right_hip"] < 140:
        feedback.append("Open hips more")
    if not feedback:
        feedback.append("Good alignment")
    return feedback


EMA_ALPHA = 0.4
PRED_WINDOW = 8
ISSUE_PERSISTENCE_FRAMES = 3
stream_state = {}

POSE_CONNECTIONS = [
    (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 12), (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (24, 26), (26, 28),
    (27, 31), (28, 32), (27, 29), (28, 30),
]

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)
os.makedirs(TTS_CACHE_DIR, exist_ok=True)


def _tts_status():
    api_key_present = bool(os.getenv("OPENAI_API_KEY"))
    package_installed = OpenAI is not None
    available = api_key_present and package_installed
    return {
        "available": available,
        "provider": "openai",
        "configured": api_key_present,
        "package_installed": package_installed,
        "model": TTS_DEFAULT_MODEL,
        "voice": TTS_DEFAULT_VOICE,
        "voice_label": "Marin",
        "format": TTS_DEFAULT_FORMAT,
    }


def _tts_media_type(response_format: str) -> str:
    return {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "opus": "audio/ogg",
        "aac": "audio/aac",
        "flac": "audio/flac",
        "pcm": "audio/L16",
    }.get(response_format, "audio/mpeg")


def _get_tts_client():
    global _tts_client
    status = _tts_status()
    if not status["configured"]:
        raise RuntimeError("OPENAI_API_KEY is not configured for backend TTS.")
    if not status["package_installed"]:
        raise RuntimeError("The OpenAI Python SDK is not installed on the backend.")
    if _tts_client is None:
        _tts_client = OpenAI()
    return _tts_client


def _build_tts_instructions(cue_type: str) -> str:
    if cue_type == "correction":
        return "\n".join([
            "Voice Affect: Warm, grounded female yoga coach.",
            "Tone: Supportive, precise, and human.",
            "Pacing: Calm but concise.",
            "Emotion: Encouraging and reassuring.",
            "Pronunciation: Enunciate pose names clearly.",
            "Pauses: Brief pause before the main correction cue.",
            "Emphasis: Stress the alignment action to change right now.",
            "Delivery: Natural spoken coaching, never robotic.",
        ])

    return "\n".join([
        "Voice Affect: Warm, human-like female yoga guide.",
        "Tone: Calm, confident, and nurturing.",
        "Pacing: Steady and spacious for guided movement.",
        "Emotion: Reassuring and present.",
        "Pronunciation: Enunciate pose names and body cues clearly.",
        "Pauses: Add gentle pauses between steps and breath prompts.",
        "Emphasis: Stress key setup actions and breath words.",
        "Delivery: Smooth premium wellness narration, not robotic.",
    ])


def _tts_cache_path(text: str, voice: str, cue_type: str, response_format: str, instructions: str) -> str:
    digest = hashlib.sha256(
        json.dumps(
            {
                "model": TTS_DEFAULT_MODEL,
                "voice": voice,
                "cue_type": cue_type,
                "response_format": response_format,
                "instructions": instructions,
                "text": text,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return os.path.join(TTS_CACHE_DIR, f"{digest}.{response_format}")


def _read_audio_response(result):
    if isinstance(result, bytes):
        return result
    if hasattr(result, "read"):
        return result.read()
    if hasattr(result, "content"):
        return result.content
    raise RuntimeError("Unexpected audio response shape from TTS provider.")


def _synthesize_tts(text: str, cue_type: str = "narration", voice: Optional[str] = None, response_format: Optional[str] = None):
    content = (text or "").strip()
    if not content:
        raise ValueError("Text is required for speech synthesis.")
    if len(content) > TTS_TEXT_LIMIT:
        raise ValueError(f"Text must be {TTS_TEXT_LIMIT} characters or fewer.")

    voice_name = voice or TTS_DEFAULT_VOICE
    audio_format = (response_format or TTS_DEFAULT_FORMAT or "mp3").lower()
    instructions = _build_tts_instructions(cue_type)
    cache_path = _tts_cache_path(content, voice_name, cue_type, audio_format, instructions)

    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return f.read(), voice_name, audio_format, True

    client = _get_tts_client()
    create_kwargs = {
        "model": TTS_DEFAULT_MODEL,
        "voice": voice_name,
        "input": content,
        "response_format": audio_format,
    }
    if "gpt-4o-mini-tts" in TTS_DEFAULT_MODEL:
        create_kwargs["instructions"] = instructions

    speech_api = client.audio.speech
    if hasattr(speech_api, "with_streaming_response"):
        with speech_api.with_streaming_response.create(**create_kwargs) as result:
            audio_bytes = result.read()
    else:
        audio_bytes = _read_audio_response(speech_api.create(**create_kwargs))

    with open(cache_path, "wb") as f:
        f.write(audio_bytes)

    return audio_bytes, voice_name, audio_format, False


def _new_session_data(now):
    return {
        "started_at": now,
        "frame_count": 0,
        "issue_frames": 0,
        "corrected_frames": 0,
        "confidence_suppressed_frames": 0,
        "total_inference_ms": 0.0,
        "transient_alert_count": 0,
        "correction_times_s": [],
        "issue_events": [],
        "open_issue_events": {},
        "persisted_issue_event_count": 0,
    }


def _safe_stream_id(stream_id: str) -> str:
    return "".join(ch if (ch.isalnum() or ch in ("-", "_")) else "_" for ch in stream_id)


def _session_paths(stream_id: str):
    sid = _safe_stream_id(stream_id)
    base = os.path.join(LOG_DIR, sid)
    os.makedirs(base, exist_ok=True)
    return {
        "base": base,
        "summary": os.path.join(base, "summary.json"),
        "events": os.path.join(base, "issue_events.jsonl"),
    }


def _write_json_atomic(path: str, payload: dict):
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)


def _append_jsonl(path: str, rows):
    if not rows:
        return
    with open(path, "a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _get_stream_state(stream_id: str, user_id: Optional[str] = None):
    now = time.time()
    # cleanup old entries
    to_delete = [k for k, v in stream_state.items() if now - v["last_seen"] > 60]
    for k in to_delete:
        del stream_state[k]

    if stream_id not in stream_state:
        stream_state[stream_id] = {
            "stream_id": stream_id,
            "ema": None,
            "pred_queue": deque(maxlen=PRED_WINDOW),
            "issue_counts": {},
            "session": _new_session_data(now),
            "last_seen": now,
            "user_id": user_id,
        }
        _persist_session_summary(stream_state[stream_id])
    stream_state[stream_id]["last_seen"] = now
    if user_id:
        stream_state[stream_id]["user_id"] = user_id
    return stream_state[stream_id]


def _load_user_profile(user_id: Optional[str]):
    if not user_id:
        return None
    return load_profile(PROFILE_DIR, user_id, create_if_missing=False)


def _safe_float(value, fallback):
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _confidence_threshold_for_pose(pose_name: Optional[str], profile: Optional[dict]) -> float:
    if not pose_name or not profile:
        return CONFIDENCE_GATE
    thresholds = profile.get("per_pose_thresholds", {})
    if not isinstance(thresholds, dict):
        return CONFIDENCE_GATE
    normalized = normalize_pose_name(pose_name)
    if normalized in thresholds:
        return _safe_float(thresholds[normalized], CONFIDENCE_GATE)
    if pose_name in thresholds:
        return _safe_float(thresholds[pose_name], CONFIDENCE_GATE)
    return CONFIDENCE_GATE


def _personalization_payload(profile: Optional[dict], pose_name: Optional[str]) -> dict:
    pose_threshold = _confidence_threshold_for_pose(pose_name, profile)
    offsets = {}
    if profile:
        offsets = {
            key: round(float(value), 2)
            for key, value in profile.get("global_angle_offsets", {}).items()
        }
    return {
        "applied": bool(offsets),
        "profile_version": profile.get("version") if profile else None,
        "pose_threshold": round(float(pose_threshold), 3),
        "angle_offsets": offsets,
    }


def _empty_coaching_payload(state=None, inference_ms=0.0):
    metrics = _session_metrics_payload(state) if state is not None else None
    return {
        "pose_name": None,
        "confidence": 0.0,
        "angles": {},
        "issues": [],
        "feedback": [],
        "bad_joints": [],
        "landmarks": [],
        "connections": POSE_CONNECTIONS,
        "confidence_gate_triggered": False,
        "metrics": metrics,
        "inference_ms": round(float(inference_ms), 2),
    }


def _no_pose_response(image_np, state=None, profile=None, inference_ms=0.0, target_pose: Optional[str] = None):
    quality = summarize_frame_quality(image_np)
    recovery_hints = build_recovery_hints(quality, pose_detected=False, confidence_suppressed=False)
    payload = _empty_coaching_payload(state=state, inference_ms=inference_ms)
    payload.update(
        {
            "error": "No pose detected",
            "guidance_mode": "recovery",
            "recovery_hints": recovery_hints,
            "quality": quality,
            "personalization": _personalization_payload(profile, None),
            "target_pose": build_target_pose_guidance(
                target_pose=target_pose,
                detected_pose=None,
                issues=[],
                confidence_suppressed=False,
            ),
        }
    )
    return payload


def _fuse_features(landmarks, state=None):
    spectral = build_pose_graph(landmarks[:, :3])
    fused = np.hstack([landmarks.flatten(), spectral]).astype(np.float32)
    if state is not None:
        if state["ema"] is None:
            state["ema"] = fused.copy()
        else:
            state["ema"] = EMA_ALPHA * fused + (1 - EMA_ALPHA) * state["ema"]
        fused = state["ema"]
    fused = scaler.transform([fused])
    return torch.tensor(fused, dtype=torch.float32).to(DEVICE)


def _apply_issue_persistence(state, issues):
    counts = state.get("issue_counts", {})
    seen = set()

    for issue in issues:
        key = f"{issue['joint']}:{issue['direction_to_fix']}"
        seen.add(key)
        counts[key] = min(counts.get(key, 0) + 1, 30)

    for key in list(counts.keys()):
        if key not in seen:
            counts[key] -= 1
            if counts[key] <= 0:
                del counts[key]

    state["issue_counts"] = counts
    stable_issues = []
    for issue in issues:
        key = f"{issue['joint']}:{issue['direction_to_fix']}"
        if counts.get(key, 0) >= ISSUE_PERSISTENCE_FRAMES:
            stable_issues.append(issue)
    return stable_issues


def _landmarks_to_payload(landmarks):
    return [
        {
            "id": idx,
            "x": float(lm[0]),
            "y": float(lm[1]),
            "visibility": float(lm[3]),
        }
        for idx, lm in enumerate(landmarks)
    ]


def _finalize_issue_episodes(session, current_keys, now_ts):
    open_events = session["open_issue_events"]
    for key in list(open_events.keys()):
        if key in current_keys:
            continue
        event = open_events.pop(key)
        duration = max(0.0, now_ts - event["start_ts"])
        event["end_ts"] = now_ts
        event["duration_s"] = round(duration, 3)
        event["resolved"] = True
        session["issue_events"].append(event)
        if duration < TRANSIENT_ALERT_S:
            session["transient_alert_count"] += 1
        else:
            session["correction_times_s"].append(duration)


def _update_session_metrics(state, pose_name, conf, issues, inference_ms, confidence_suppressed=False):
    session = state["session"]
    now_ts = time.time()
    session["frame_count"] += 1
    session["total_inference_ms"] += float(inference_ms)

    if confidence_suppressed:
        session["confidence_suppressed_frames"] += 1
        _finalize_issue_episodes(session, set(), now_ts)
        _persist_issue_events(state)
        if session["frame_count"] % SUMMARY_PERSIST_EVERY_FRAMES == 0:
            _persist_session_summary(state)
        return

    if issues:
        session["issue_frames"] += 1
    else:
        session["corrected_frames"] += 1

    issue_keys = set()
    for issue in issues:
        key = f"{issue['joint']}:{issue['direction_to_fix']}"
        issue_keys.add(key)
        if key not in session["open_issue_events"]:
            session["open_issue_events"][key] = {
                "key": key,
                "pose_name": pose_name,
                "start_ts": now_ts,
                "first_confidence": round(float(conf), 4),
            }
    _finalize_issue_episodes(session, issue_keys, now_ts)
    _persist_issue_events(state)
    if session["frame_count"] % SUMMARY_PERSIST_EVERY_FRAMES == 0:
        _persist_session_summary(state)


def _session_metrics_payload(state):
    session = state["session"]
    now_ts = time.time()
    elapsed_s = max(1.0, now_ts - session["started_at"])
    elapsed_min = elapsed_s / 60.0
    frame_count = max(1, session["frame_count"])
    avg_latency = session["total_inference_ms"] / frame_count
    false_alerts_per_min = session["transient_alert_count"] / elapsed_min
    correction_times = session["correction_times_s"]
    avg_time_to_correct = (sum(correction_times) / len(correction_times)) if correction_times else None

    return {
        "frames": session["frame_count"],
        "avg_latency_ms": round(avg_latency, 2),
        "false_alerts_per_min": round(false_alerts_per_min, 3),
        "avg_time_to_correct_s": round(avg_time_to_correct, 3) if avg_time_to_correct is not None else None,
        "issue_frames": session["issue_frames"],
        "corrected_frames": session["corrected_frames"],
        "confidence_suppressed_frames": session["confidence_suppressed_frames"],
        "active_issue_events": len(session["open_issue_events"]),
        "resolved_issue_events": len(session["issue_events"]),
    }


def _persist_issue_events(state):
    if state["stream_id"].startswith("__"):
        return
    session = state["session"]
    start_idx = session.get("persisted_issue_event_count", 0)
    events = session["issue_events"][start_idx:]
    if not events:
        return
    paths = _session_paths(state["stream_id"])
    _append_jsonl(paths["events"], events)
    session["persisted_issue_event_count"] = len(session["issue_events"])


def _persist_session_summary(state):
    if state["stream_id"].startswith("__"):
        return
    paths = _session_paths(state["stream_id"])
    payload = {
        "stream_id": state["stream_id"],
        "updated_at": time.time(),
        "metrics": _session_metrics_payload(state),
    }
    if state.get("user_id"):
        payload["user_id"] = state["user_id"]
    _write_json_atomic(paths["summary"], payload)


def _bad_joints_from_issues(issues):
    return sorted({issue["joint"] for issue in issues})


def _process_realtime_output(
    landmarks,
    pose_name,
    conf,
    state,
    inference_ms,
    profile=None,
    quality=None,
    target_pose: Optional[str] = None,
):
    angles = extract_angles(landmarks)
    pose_threshold = _confidence_threshold_for_pose(pose_name, profile)
    confidence_suppressed = conf < pose_threshold
    angle_offsets = (profile or {}).get("global_angle_offsets", {})

    if confidence_suppressed:
        stable_issues = []
        feedback = ["Hold steady so I can detect your posture clearly."]
    else:
        issues = build_pose_issues(pose_name, angles, angle_offsets=angle_offsets)
        stable_issues = _apply_issue_persistence(state, issues)
        feedback = [issue["message"] for issue in stable_issues[:2]] or ["Good alignment"]

    quality = quality or {}
    recovery_hints = build_recovery_hints(
        quality,
        pose_detected=True,
        confidence_suppressed=confidence_suppressed,
    )
    guidance_mode = "recovery" if confidence_suppressed else "coaching"

    _update_session_metrics(
        state=state,
        pose_name=pose_name,
        conf=conf,
        issues=stable_issues,
        inference_ms=inference_ms,
        confidence_suppressed=confidence_suppressed,
    )

    return {
        "angles": angles,
        "issues": stable_issues[:3],
        "feedback": feedback[:2],
        "bad_joints": _bad_joints_from_issues(stable_issues),
        "landmarks": _landmarks_to_payload(landmarks),
        "connections": POSE_CONNECTIONS,
        "confidence_gate_triggered": confidence_suppressed,
        "metrics": _session_metrics_payload(state),
        "inference_ms": round(float(inference_ms), 2),
        "guidance_mode": guidance_mode,
        "recovery_hints": recovery_hints,
        "quality": quality,
        "personalization": _personalization_payload(profile, pose_name),
        "target_pose": build_target_pose_guidance(
            target_pose=target_pose,
            detected_pose=pose_name,
            issues=stable_issues,
            confidence_suppressed=confidence_suppressed,
        ),
    }

# ============================================================
# FEATURE EXTRACTION FUNCTION
# ============================================================
def extract_features(image: np.ndarray):
    """Extract keypoints + spectral graph features for inference."""
    results = pose_detector.process(image)
    if not results.pose_landmarks:
        return None

    landmarks = np.array([[lm.x, lm.y, lm.z, lm.visibility] for lm in results.pose_landmarks.landmark])
    spectral_feats = build_pose_graph(landmarks[:, :3])
    fused_features = np.hstack([landmarks.flatten(), spectral_feats])
    fused_features = scaler.transform([fused_features])
    return torch.tensor(fused_features, dtype=torch.float32).to(DEVICE)

# ============================================================
# FASTAPI SETUP
# ============================================================
app = FastAPI(title="YogaPoseFusion v4 Ensemble API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "YogaPoseFusion v4 Ensemble Inference API running ✅",
        "device": str(DEVICE),
        "models_loaded": len(models),
        "input_dim": input_dim,
        "guided_pose_count": len(pose_catalog()),
        "tts": _tts_status(),
    }


@app.get("/poses/catalog")
def get_pose_catalog():
    return {"poses": pose_catalog()}


@app.get("/poses/reference-image/{pose_slug}")
def get_pose_reference_image(pose_slug: str):
    pose = resolve_pose_by_slug(pose_slug)
    if not pose:
        raise HTTPException(status_code=404, detail="Pose not found.")

    image_path = reference_image_path_for_pose(pose)
    if not image_path or not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Reference image not available.")

    return FileResponse(image_path)


@app.post("/recommendations")
def get_recommendations(payload: dict = Body(default={})):
    return build_recommendation_plan(payload)


@app.post("/tts")
def synthesize_tts(payload: dict = Body(default={})):
    status = _tts_status()
    if not status["available"]:
        reason = (
            "Backend TTS requires OPENAI_API_KEY and the OpenAI Python SDK."
            if not status["configured"] or not status["package_installed"]
            else "Backend TTS is unavailable."
        )
        raise HTTPException(status_code=503, detail=reason)

    text = (payload.get("text") or "").strip()
    cue_type = (payload.get("cue_type") or "narration").strip().lower()
    voice = (payload.get("voice") or status["voice"]).strip()
    response_format = (payload.get("response_format") or status["format"]).strip().lower()

    try:
        audio_bytes, resolved_voice, resolved_format, cached = _synthesize_tts(
            text=text,
            cue_type=cue_type,
            voice=voice,
            response_format=response_format,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"TTS synthesis failed: {error}") from error

    return Response(
        content=audio_bytes,
        media_type=_tts_media_type(resolved_format),
        headers={
            "X-TTS-Provider": status["provider"],
            "X-TTS-Model": status["model"],
            "X-TTS-Voice": resolved_voice,
            "X-TTS-Cached": "true" if cached else "false",
        },
    )


@app.get("/profile/{user_id}")
def get_profile(user_id: str):
    profile = load_profile(PROFILE_DIR, user_id, create_if_missing=False)
    return {
        "user_id": user_id,
        "has_profile": profile is not None,
        "profile": profile_summary(profile),
    }


@app.post("/profile/{user_id}/calibration/frame")
async def calibration_frame(
    user_id: str,
    file: UploadFile = File(...),
    step_id: str = Form("neutral"),
):
    try:
        if step_id not in CALIBRATION_STEPS:
            return {
                "accepted": False,
                "error": f"Unsupported calibration step: {step_id}",
                "step_id": step_id,
                "supported_steps": list(CALIBRATION_STEPS.keys()),
            }

        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
        image_np = np.array(image)
        results = pose_detector.process(image_np)
        if not results.pose_landmarks:
            quality = summarize_frame_quality(image_np)
            return {
                "accepted": False,
                "error": "No pose detected",
                "step_id": step_id,
                "samples_collected": 0,
                "samples_required": CALIBRATION_SAMPLES_REQUIRED,
                "ready_for_next_step": False,
                "quality": quality,
                "recovery_hints": build_recovery_hints(quality, pose_detected=False),
            }

        landmarks = np.array([
            [lm.x, lm.y, lm.z, lm.visibility]
            for lm in results.pose_landmarks.landmark
        ])
        quality = summarize_frame_quality(image_np, landmarks)
        if not quality.get("full_body_visible"):
            profile = load_profile(PROFILE_DIR, user_id, create_if_missing=False)
            existing_profile = profile_summary(profile)
            samples_collected = 0
            if existing_profile:
                samples_collected = existing_profile["step_progress"].get(step_id, {}).get("sample_count", 0)
            return {
                "accepted": False,
                "error": "Frame quality too low for calibration",
                "step_id": step_id,
                "samples_collected": samples_collected,
                "samples_required": CALIBRATION_SAMPLES_REQUIRED,
                "ready_for_next_step": False,
                "quality": quality,
                "recovery_hints": build_recovery_hints(quality, pose_detected=True),
            }

        profile = load_profile(PROFILE_DIR, user_id, create_if_missing=True)
        step_state = update_calibration_step(profile, step_id, extract_angles(landmarks), quality)
        save_profile(PROFILE_DIR, user_id, profile)

        return {
            "accepted": True,
            "step_id": step_id,
            "samples_collected": int(step_state["sample_count"]),
            "samples_required": int(profile["calibration"]["required_samples"]),
            "ready_for_next_step": int(step_state["sample_count"]) >= int(profile["calibration"]["required_samples"]),
            "quality": quality,
            "recovery_hints": [],
            "profile": profile_summary(profile),
        }
    except Exception as e:
        return {"accepted": False, "error": str(e), "step_id": step_id}


@app.post("/profile/{user_id}/calibration/complete")
def calibration_complete(user_id: str):
    try:
        profile = load_profile(PROFILE_DIR, user_id, create_if_missing=False)
        if profile is None:
            return {"status": "missing_profile", "user_id": user_id, "profile_summary": None}
        finalize_profile(profile)
        save_profile(PROFILE_DIR, user_id, profile)
        status = "ready" if profile.get("completed_steps") else "needs_more_data"
        return {
            "status": status,
            "profile_summary": profile_summary(profile),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ============================================================
# SINGLE IMAGE INFERENCE
# ============================================================
@app.post("/predict")
async def predict_pose(file: UploadFile = File(...)):
    try:
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
        image_np = np.array(image)
        features = extract_features(image_np)

        if features is None:
            return {"error": "No pose landmarks detected. Ensure full body is visible."}

        with torch.no_grad():
            # Ensemble average
            outputs = torch.stack([m(features) for m in models]).mean(dim=0)
            probs = torch.softmax(outputs, dim=1)
            conf, pred_class = torch.max(probs, dim=1)
            pose_name = idx_to_pose.get(str(pred_class.item()), "Unknown Pose")

        return {
            "pose_name": pose_name,
            "predicted_class": int(pred_class.item()),
            "confidence": float(conf.item())
        }

    except Exception as e:
        return {"error": str(e)}

# ============================================================
# MULTI-IMAGE (BATCH) INFERENCE
# ============================================================
@app.post("/predict_batch")
async def predict_batch(files: list[UploadFile] = File(...)):
    results = []
    for file in files:
        try:
            image = Image.open(io.BytesIO(await file.read())).convert("RGB")
            image_np = np.array(image)
            features = extract_features(image_np)
            if features is None:
                results.append({"file": file.filename, "error": "No pose detected"})
                continue

            with torch.no_grad():
                outputs = torch.stack([m(features) for m in models]).mean(dim=0)
                probs = torch.softmax(outputs, dim=1)
                conf, pred_class = torch.max(probs, dim=1)
                pose_name = idx_to_pose.get(str(pred_class.item()), "Unknown Pose")

            results.append({
                "file": file.filename,
                "pose_name": pose_name,
                "predicted_class": int(pred_class.item()),
                "confidence": float(conf.item())
            })
        except Exception as e:
            results.append({"file": file.filename, "error": str(e)})

    return {"results": results}
    
# ============================================================
# REAL-TIME FEEDBACK
# ============================================================
@app.post("/realtime_feedback")
async def realtime_pose_feedback(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    target_pose: Optional[str] = Form(None),
):
    try:
        started = time.perf_counter()
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
        image_np = np.array(image)
        profile = _load_user_profile(user_id)

        results = pose_detector_video.process(image_np)
        if not results.pose_landmarks:
            return _no_pose_response(
                image_np,
                profile=profile,
                inference_ms=(time.perf_counter() - started) * 1000.0,
                target_pose=target_pose,
            )

        landmarks = np.array([
            [lm.x, lm.y, lm.z, lm.visibility]
            for lm in results.pose_landmarks.landmark
        ])
        quality = summarize_frame_quality(image_np, landmarks)

        # --- Classification ---
        fused = _fuse_features(landmarks, state=None)

        with torch.no_grad():
            outputs = torch.stack([m(fused) for m in models]).mean(dim=0)
            probs = torch.softmax(outputs, dim=1)
            conf, pred_class = torch.max(probs, dim=1)
            conf = float(conf.item())

        pose_name = idx_to_pose.get(str(pred_class.item()), "Unknown Pose")

        temp_state = {
            "stream_id": "__single_frame__",
            "issue_counts": {},
            "session": _new_session_data(time.time()),
            "user_id": user_id,
        }
        inference_ms = (time.perf_counter() - started) * 1000.0
        coaching = _process_realtime_output(
            landmarks=landmarks,
            pose_name=pose_name,
            conf=conf,
            state=temp_state,
            inference_ms=inference_ms,
            profile=profile,
            quality=quality,
            target_pose=target_pose,
        )

        return {
            "pose_name": pose_name,
            "confidence": conf,
            "angles": coaching["angles"],
            "issues": coaching["issues"],
            "corrections": coaching["feedback"],
            "feedback": coaching["feedback"],
            "bad_joints": coaching["bad_joints"],
            "landmarks": coaching["landmarks"],
            "connections": coaching["connections"],
            "confidence_gate_triggered": coaching["confidence_gate_triggered"],
            "metrics": coaching["metrics"],
            "inference_ms": coaching["inference_ms"],
            "guidance_mode": coaching["guidance_mode"],
            "recovery_hints": coaching["recovery_hints"],
            "quality": coaching["quality"],
            "personalization": coaching["personalization"],
            "target_pose": coaching["target_pose"],
        }

    except Exception as e:
        return {"error": str(e)}


# ============================================================
# REAL-TIME FRAME (REST STREAMING)
# ============================================================
@app.post("/realtime_frame")
async def realtime_frame(
    file: UploadFile = File(...),
    stream_id: str = Form("default"),
    user_id: Optional[str] = Form(None),
    target_pose: Optional[str] = Form(None),
):
    try:
        started = time.perf_counter()
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
        image_np = np.array(image)
        profile = _load_user_profile(user_id)
        state = _get_stream_state(stream_id, user_id=user_id)
        results = pose_detector_video.process(image_np)
        if not results.pose_landmarks:
            return _no_pose_response(
                image_np,
                state=state,
                profile=profile,
                inference_ms=(time.perf_counter() - started) * 1000.0,
                target_pose=target_pose,
            )

        landmarks = np.array([
            [lm.x, lm.y, lm.z, lm.visibility]
            for lm in results.pose_landmarks.landmark
        ])
        quality = summarize_frame_quality(image_np, landmarks)

        fused = _fuse_features(landmarks, state=state)

        with torch.no_grad():
            outputs = torch.stack([m(fused) for m in models]).mean(dim=0)
            probs = torch.softmax(outputs, dim=1)
            conf, pred_class = torch.max(probs, dim=1)
            pred_class = int(pred_class.item())
            conf = float(conf.item())

        state["pred_queue"].append(pred_class)
        pred_class = Counter(state["pred_queue"]).most_common(1)[0][0]
        pose_name = idx_to_pose.get(str(pred_class), "Unknown Pose")
        inference_ms = (time.perf_counter() - started) * 1000.0
        coaching = _process_realtime_output(
            landmarks=landmarks,
            pose_name=pose_name,
            conf=conf,
            state=state,
            inference_ms=inference_ms,
            profile=profile,
            quality=quality,
            target_pose=target_pose,
        )

        return {
            "pose_name": pose_name,
            "confidence": conf,
            "issues": coaching["issues"],
            "feedback": coaching["feedback"],
            "bad_joints": coaching["bad_joints"],
            "landmarks": coaching["landmarks"],
            "connections": coaching["connections"],
            "confidence_gate_triggered": coaching["confidence_gate_triggered"],
            "metrics": coaching["metrics"],
            "inference_ms": coaching["inference_ms"],
            "guidance_mode": coaching["guidance_mode"],
            "recovery_hints": coaching["recovery_hints"],
            "quality": coaching["quality"],
            "personalization": coaching["personalization"],
            "target_pose": coaching["target_pose"],
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# REAL-TIME WS STREAMING
# ============================================================
@app.websocket("/ws/realtime")
async def ws_realtime(
    websocket: WebSocket,
    stream_id: str = "default",
    user_id: Optional[str] = None,
    target_pose: Optional[str] = None,
):
    await websocket.accept()
    state = _get_stream_state(stream_id, user_id=user_id)
    profile = _load_user_profile(user_id)
    try:
        while True:
            started = time.perf_counter()
            payload = await websocket.receive_text()
            # payload can be raw base64 or JSON with {"b64": "..."}
            if payload.strip().startswith("{"):
                msg = json.loads(payload)
                b64 = msg.get("b64", "")
                message_target_pose = msg.get("target_pose", target_pose)
            else:
                b64 = payload
                message_target_pose = target_pose

            image_bytes = base64.b64decode(b64)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image_np = np.array(image)
            results = pose_detector_video.process(image_np)
            if not results.pose_landmarks:
                await websocket.send_json(
                    _no_pose_response(
                        image_np,
                        state=state,
                        profile=profile,
                        inference_ms=(time.perf_counter() - started) * 1000.0,
                        target_pose=message_target_pose,
                    )
                )
                continue

            landmarks = np.array([
                [lm.x, lm.y, lm.z, lm.visibility]
                for lm in results.pose_landmarks.landmark
            ])
            quality = summarize_frame_quality(image_np, landmarks)

            fused = _fuse_features(landmarks, state=state)
            with torch.no_grad():
                outputs = torch.stack([m(fused) for m in models]).mean(dim=0)
                probs = torch.softmax(outputs, dim=1)
                conf, pred_class = torch.max(probs, dim=1)
                pred_class = int(pred_class.item())
                conf = float(conf.item())

            state["pred_queue"].append(pred_class)
            pred_class = Counter(state["pred_queue"]).most_common(1)[0][0]
            pose_name = idx_to_pose.get(str(pred_class), "Unknown Pose")
            inference_ms = (time.perf_counter() - started) * 1000.0
            coaching = _process_realtime_output(
                landmarks=landmarks,
                pose_name=pose_name,
                conf=conf,
                state=state,
                inference_ms=inference_ms,
                profile=profile,
                quality=quality,
                target_pose=message_target_pose,
            )

            await websocket.send_json({
                "pose_name": pose_name,
                "confidence": conf,
                "issues": coaching["issues"],
                "feedback": coaching["feedback"],
                "bad_joints": coaching["bad_joints"],
                "landmarks": coaching["landmarks"],
                "connections": coaching["connections"],
                "confidence_gate_triggered": coaching["confidence_gate_triggered"],
                "metrics": coaching["metrics"],
                "inference_ms": coaching["inference_ms"],
                "guidance_mode": coaching["guidance_mode"],
                "recovery_hints": coaching["recovery_hints"],
                "quality": coaching["quality"],
                "personalization": coaching["personalization"],
                "target_pose": coaching["target_pose"],
            })
    except Exception:
        return


@app.get("/session/{stream_id}/summary")
def session_summary(stream_id: str):
    state = stream_state.get(stream_id)
    if not state:
        return {"error": "Session not found"}
    _persist_session_summary(state)
    return {
        "stream_id": stream_id,
        "metrics": _session_metrics_payload(state),
    }


@app.post("/session/{stream_id}/reset")
def session_reset(stream_id: str):
    now = time.time()
    stream_state[stream_id] = {
        "stream_id": stream_id,
        "ema": None,
        "pred_queue": deque(maxlen=PRED_WINDOW),
        "issue_counts": {},
        "session": _new_session_data(now),
        "last_seen": now,
        "user_id": stream_state.get(stream_id, {}).get("user_id"),
    }
    _persist_session_summary(stream_state[stream_id])
    return {"status": "reset", "stream_id": stream_id}

# ============================================================
# RUN LOCALLY
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
