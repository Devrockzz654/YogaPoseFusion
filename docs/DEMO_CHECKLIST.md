## Final Demo Checklist

### Pre-Demo (10-15 min before)
1. Start backend:
```bash
cd /Volumes/Dev/Project2/YogaPoseFusion/backend
uvicorn inference:app --host 0.0.0.0 --port 8000
```
2. Start frontend:
```bash
cd /Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend
npm start
```
3. Open `http://localhost:3000`.
4. Confirm API status is `Connected`.
5. Ensure webcam permission is granted.

### Demo Flow
1. Show static image prediction (`Upload Image` + classify).
2. Start camera.
3. Start real-time coaching (`Start Real-time`).
4. Perform one correct pose and show:
   - `Good alignment`
   - low/no issue markers.
5. Intentionally break posture (e.g., bend knee too much) and show:
   - specific correction message
   - red highlighted bad joints
   - focus joint + direction.
6. Correct posture and show:
   - issue clears
   - feedback improves.
7. Point out metrics panel:
   - latency
   - false alerts/min
   - time-to-correct.

### Session Evidence
1. Reset session:
```bash
curl -X POST http://localhost:8000/session/web_ui_<id>/reset
```
2. Fetch summary:
```bash
curl http://localhost:8000/session/web_ui_<id>/summary
```
3. Show persisted files:
- `backend/logs/sessions/<stream_id>/summary.json`
- `backend/logs/sessions/<stream_id>/issue_events.jsonl`

### Backup Plan
1. If WebSocket is unstable, use `Start REST`.
2. If pose not detected:
   - increase lighting
   - move full body into frame
   - hold pose 1-2 seconds.
3. If corrections seem noisy:
   - keep pose steady
   - use a simpler pose (e.g., Chair, Plank, Warrior II).
