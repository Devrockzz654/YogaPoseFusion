# API Documentation

Base URL for local development:

```text
http://localhost:8000
```

## Health

### `GET /`

Returns backend status and model information.

Typical fields:

- `status`
- `device`
- `models_loaded`
- `input_dim`
- `guided_pose_count`
- `tts`

`tts` includes:

- `available`
- `provider`
- `configured`
- `package_installed`
- `model`
- `voice`
- `voice_label`
- `format`

## Guided Practice Catalog

### `GET /poses/catalog`

Returns the pose catalog used by the frontend.

### `GET /poses/reference-image/{pose_slug}`

Returns the reference image for a guided pose slug when available.

## Recommendations

### `POST /recommendations`

Builds a personalized yoga routine from a user profile.

JSON body:

- `age`
- `experience_level`
- `session_minutes`
- `goals[]`
- `health_factors[]`

Typical response sections:

- `summary`
- `featured_recommendations[]`
- `recommendations[]`
- `safety_notes[]`
- `disclaimer`

## Voice Synthesis

### `POST /tts`

Generates an audio coaching clip when TTS is configured.

JSON body:

- `text`
- `cue_type`
- `voice` optional
- `response_format` optional

Success returns an audio response stream and response headers such as:

- `X-TTS-Provider`
- `X-TTS-Model`
- `X-TTS-Voice`
- `X-TTS-Cached`

## Profile And Calibration

### `GET /profile/{user_id}`

Returns the current user profile or calibration summary for a user id.

### `POST /profile/{user_id}/calibration/frame`

Collects one calibration frame.

Form fields:

- `file`
- `step_id`

### `POST /profile/{user_id}/calibration/complete`

Finalizes calibration and stores personalized offsets.

## Image Inference

### `POST /predict`

Single-image pose classification.

Form fields:

- `file`

### `POST /predict_batch`

Batch image classification.

Form fields:

- `files`

## Realtime Coaching

### `POST /realtime_feedback`

Single-frame coaching response.

Form fields:

- `file`
- `user_id` optional
- `target_pose` optional

Typical response fields:

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

### `POST /realtime_frame`

REST polling mode for live webcam frames.

Form fields:

- `file`
- `stream_id`
- `user_id` optional
- `target_pose` optional

### `WS /ws/realtime`

Realtime WebSocket coaching endpoint.

Common query params:

- `stream_id`
- `user_id`
- `target_pose`

Input:

- base64 image string
- or JSON containing base64 image content

## Session Endpoints

### `GET /session/{stream_id}/summary`

Returns the current session metrics summary.

### `POST /session/{stream_id}/reset`

Resets the in-memory state for a session id.

## Notes

- The backend currently supports both recommendation and live coaching workflows.
- The frontend uses these endpoints through `yoga-pose-fusion-frontend/src/services/api.js`.
- TTS behavior depends on backend environment configuration.
