# Demo Checklist

## Before The Demo

1. Start the backend:

```bash
cd backend
uvicorn inference:app --host 0.0.0.0 --port 8000
```

2. Start the frontend:

```bash
cd yoga-pose-fusion-frontend
npm start
```

3. Open `http://localhost:3000`
4. Confirm the backend root responds at `http://localhost:8000/`
5. Allow webcam permission in the browser

## Suggested Demo Flow

1. Show the landing page and auth panel
2. Register or log in
3. Walk through the Journey tab
4. Enter age, experience level, goals, and health factors
5. Generate recommendations
6. Show the recommended routine and ranked pose library
7. Open Live Coach for one selected pose
8. Test one aligned posture and one intentionally incorrect posture

## Useful Backend Checks

Health check:

```bash
curl http://localhost:8000/
```

Pose catalog:

```bash
curl http://localhost:8000/poses/catalog
```

Session reset:

```bash
curl -X POST http://localhost:8000/session/demo/reset
```

## Backup Plan

- If Google login is unavailable, use the local form-based auth
- If webcam flow is unstable, use a single-frame upload flow in Live Coach
- If TTS is unavailable, continue without voice and focus on visual feedback
- If pose detection is weak, improve lighting and keep the whole body inside the frame
