## Setup Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- npm
- Webcam

### 2. Backend Setup
From `/Volumes/Dev/Project2/YogaPoseFusion`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn numpy torch mediapipe pillow joblib networkx scipy scikit-learn python-multipart
```

Notes:
- If you already have a working Conda env, use it instead.
- Model files must exist in `backend/models/`.

### 3. Start Backend
```bash
cd /Volumes/Dev/Project2/YogaPoseFusion/backend
uvicorn inference:app --host 0.0.0.0 --port 8000 --reload
```

Backend should be available at:
- `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### 4. Frontend Setup
```bash
cd /Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend
npm install
npm start
```

Frontend default URL:
- `http://localhost:3000`

### 5. Realtime Coaching Test
1. Open frontend.
2. Click `Start Camera`.
3. Click `Start Real-time` (WebSocket) or `Start REST`.
4. Check:
   - live feedback
   - red highlighted bad joints
   - coaching metrics panel
   - optional voice cues

### 6. Session Logs
Realtime sessions are persisted under:
- `/Volumes/Dev/Project2/YogaPoseFusion/backend/logs/sessions/<stream_id>/summary.json`
- `/Volumes/Dev/Project2/YogaPoseFusion/backend/logs/sessions/<stream_id>/issue_events.jsonl`

### 7. Common Issues
- `No pose detected`: ensure full body is visible and lighting is sufficient.
- Camera permission denied: allow browser camera access.
- High false alerts: increase confidence gate or widen pose rule ranges.
