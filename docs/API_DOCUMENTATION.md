## API Documentation

Base URL: `http://localhost:8000`

### Health
#### `GET /`
Returns API status and model/device info.

Response fields:
- `status`
- `device`
- `models_loaded`
- `input_dim`
- `guided_pose_count`
- `tts`
  - `available`
  - `provider`
  - `configured`
  - `package_installed`
  - `model`
  - `voice`
  - `voice_label`
  - `format`

### Voice Synthesis
#### `POST /tts`
Synthesizes a spoken coaching clip using the dedicated backend TTS provider.

JSON body:
- `text`
- `cue_type`: `narration` or `correction`
- `voice`: optional override, defaults to the configured female coach voice
- `response_format`: optional, defaults to `mp3`

Success response:
- binary audio stream with `audio/*` content type
- response headers include `X-TTS-Provider`, `X-TTS-Model`, `X-TTS-Voice`, `X-TTS-Cached`

Failure cases:
- `400` if `text` is missing or too long
- `503` if backend TTS is not configured
- `502` if synthesis fails upstream

### Guided Practice Catalog
#### `GET /poses/catalog`
Returns the coachable pose library used by the website.

Response fields:
- `poses[]`
  - `pose_name`
  - `sanskrit_name`
  - `difficulty`
  - `intensity`
  - `slug`
  - `coach_focus`
  - `benefits[]`
  - `instructions[]`
  - `breath_cues[]`
  - `common_mistakes[]`
  - `modifications[]`
  - `caution`

### Recommendations
#### `POST /recommendations`
Generates a personalized asana routine from user age, experience, goals, and health factors.

JSON body:
- `age`
- `experience_level`
- `session_minutes`
- `health_factors[]`
- `goals[]`

Response fields:
- `summary`
- `recommendations[]`
  - `pose_name`
  - `sanskrit_name`
  - `difficulty`
  - `hold_seconds`
  - `repetitions`
  - `benefits[]`
  - `instructions[]`
  - `breath_cues[]`
  - `common_mistakes[]`
  - `modifications[]`
  - `coach_focus`
  - `why_selected`
  - `matched_goals[]`
  - `matched_health_factors[]`
  - `caution`
- `safety_notes[]`
- `disclaimer`

### Personalization Endpoints
#### `GET /profile/{user_id}`
Returns profile existence and the current calibration summary for that user.

#### `POST /profile/{user_id}/calibration/frame`
Collects one calibration frame for a step.

Form fields:
- `file`: image frame
- `step_id`: one of `neutral`, `chair`, `warrior_ii`

Response fields:
- `accepted`
- `step_id`
- `samples_collected`
- `samples_required`
- `ready_for_next_step`
- `quality`
- `recovery_hints[]`
- `profile`

#### `POST /profile/{user_id}/calibration/complete`
Finalizes the profile and computes personalized angle offsets.

### Inference Endpoints
#### `POST /predict`
Single-image classification.

Form fields:
- `file`: image file

Response:
- `pose_name`
- `predicted_class`
- `confidence`

#### `POST /predict_batch`
Batch image classification.

Form fields:
- `files`: multiple image files

Response:
- `results[]` with pose/confidence or error per file.

### Realtime Coaching
#### `POST /realtime_feedback`
Single-frame feedback payload (debug/useful for integration tests).

Form fields:
- `file`: image frame
- `user_id`: optional profile id for personalized thresholds/offsets
- `target_pose`: optional pose name from the guided routine

Response fields:
- `pose_name`
- `confidence`
- `angles`
- `issues[]`
- `feedback[]`
- `bad_joints[]`
- `landmarks[]`
- `connections[]`
- `confidence_gate_triggered`
- `guidance_mode`
- `recovery_hints[]`
- `quality`
- `personalization`
- `target_pose`
- `metrics`
- `inference_ms`

#### `POST /realtime_frame`
REST polling mode for live frames.

Form fields:
- `file`: frame image
- `stream_id`: session id (used for smoothing/logging/metrics)
- `user_id`: optional profile id for personalized thresholds/offsets
- `target_pose`: optional pose name from the guided routine

Response fields (same core schema as `/realtime_feedback`):
- `pose_name`, `confidence`, `issues`, `feedback`, `bad_joints`,
  `landmarks`, `connections`, `confidence_gate_triggered`, `guidance_mode`,
  `recovery_hints`, `quality`, `personalization`, `target_pose`, `metrics`, `inference_ms`

#### `WS /ws/realtime?stream_id=<id>&user_id=<id>`
WebSocket realtime coaching mode.

Input:
- send base64 image string per message (or JSON with `{ "b64": "..." }`)
- optional `target_pose` can be provided as a query param or inside the JSON payload

Output message:
- `pose_name`
- `confidence`
- `issues[]`
- `feedback[]`
- `bad_joints[]`
- `landmarks[]`
- `connections[]`
- `confidence_gate_triggered`
- `guidance_mode`
- `recovery_hints[]`
- `quality`
- `personalization`
- `target_pose`
- `metrics`
- `inference_ms`

### `target_pose` Object Schema
When a guided pose is supplied, responses include:
- `requested_pose`
- `pose_name`
- `sanskrit_name`
- `available`
- `status`
  - `aligned`
  - `needs_correction`
  - `different_pose`
  - `hold_steady`
  - `awaiting_pose`
- `matched_detected_pose`
- `message`
- `coach_focus`
- `instructions[]`
- `breath_cues[]`
- `common_mistakes[]`
- `modifications[]`
- `caution`

### Session Endpoints
#### `GET /session/{stream_id}/summary`
Returns current metrics for that session and writes `summary.json`.

#### `POST /session/{stream_id}/reset`
Resets in-memory session state and restarts metrics for `stream_id`.

### `issues[]` Object Schema
Each issue contains:
- `joint` (e.g. `left_knee`)
- `angle_key`
- `current_angle`
- `target_range` (string like `80-130`)
- `direction_to_fix` (`increase` or `decrease`)
- `severity`
- `priority`
- `message`

### Notes
- Corrections are suppressed when confidence is below threshold (`CONFIDENCE_GATE`).
- Personalized profiles may shift angle ranges and override thresholds per pose.
- `metrics.false_alerts_per_min` is based on short issue episodes (`TRANSIENT_ALERT_S`).
- Session logs are stored under:
  - `backend/logs/sessions/<stream_id>/summary.json`
  - `backend/logs/sessions/<stream_id>/issue_events.jsonl`
