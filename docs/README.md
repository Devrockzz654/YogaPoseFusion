## YogaPoseFusion

Real-time yoga posture coaching system using:
- MediaPipe pose landmarks
- Spectral + keypoint fusion model (PyTorch ensemble)
- FastAPI realtime backend (REST + WebSocket)
- React webcam UI with live skeleton overlay, bad-joint highlighting, voice cues

### Current Capabilities
- Pose classification from image and webcam frames
- Real-time corrective feedback with pose-aware rules
- User calibration profiles with personalized angle offsets
- Recovery guidance for low-confidence or poor-framing frames
- Confidence gating to suppress unreliable corrections
- Temporal persistence filtering to reduce flicker/noisy alerts
- Session coaching metrics:
  - average latency (ms)
  - false alerts per minute
  - average time-to-correct (seconds)
- Persistent session logs on backend:
  - `backend/logs/sessions/<stream_id>/summary.json`
  - `backend/logs/sessions/<stream_id>/issue_events.jsonl`

### Project Structure
- `backend/inference.py`: main API + realtime coaching pipeline
- `backend/models/pose_correction.py`: pose-specific correction rules
- `backend/models/personalization.py`: calibration profile storage and offsets
- `backend/models/frame_quality.py`: framing/lighting quality heuristics
- `backend/models/pose_graph_spectral.py`: spectral feature extraction
- `backend/models/*.pt`: trained ensemble checkpoints
- `scripts/*.ipynb`: preprocessing/training/inference notebooks
- `yoga-pose-fusion-frontend/`: React live UI

### Quick Start
See `/Volumes/Dev/Project2/YogaPoseFusion/docs/SETUP_GUIDE.md`.

### API
See `/Volumes/Dev/Project2/YogaPoseFusion/docs/API_DOCUMENTATION.md`.

### Demo Workflow
See `/Volumes/Dev/Project2/YogaPoseFusion/docs/DEMO_CHECKLIST.md`.
