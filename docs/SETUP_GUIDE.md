# Setup Guide

## 1. Prerequisites

- Python 3.10+
- Node.js 20+ recommended
- npm
- Webcam access for live coaching

## 2. Backend Setup

From the repo root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Start the backend:

```bash
uvicorn inference:app --host 0.0.0.0 --port 8000 --reload
```

Backend URLs:

- `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

## 3. Frontend Setup

From the repo root:

```bash
cd yoga-pose-fusion-frontend
npm install
npm start
```

Frontend URL:

- `http://localhost:3000`

## 4. Frontend Environment Variables

The frontend reads configuration from `.env` values based on `.env.example`.

Minimum local value:

```text
REACT_APP_API_BASE_URL=http://localhost:8000
```

Optional Firebase values for Google sign-in:

- `REACT_APP_FIREBASE_API_KEY`
- `REACT_APP_FIREBASE_AUTH_DOMAIN`
- `REACT_APP_FIREBASE_PROJECT_ID`
- `REACT_APP_FIREBASE_STORAGE_BUCKET`
- `REACT_APP_FIREBASE_MESSAGING_SENDER_ID`
- `REACT_APP_FIREBASE_APP_ID`

If Firebase values are missing, the app still supports the local form-based login/register flow.

## 5. Local Verification

After both frontend and backend are running:

1. open `http://localhost:3000`
2. register or log in with the local form
3. optionally test Google sign-in if Firebase is configured
4. generate recommendations from the Journey tab
5. move to Live Coach and confirm backend status is reachable

## 6. Common Local Issues

- `No pose detected`
  Ensure the full body is visible and the frame has enough lighting.

- `Camera permission denied`
  Allow camera access in the browser.

- `auth/api-key-not-valid`
  Re-check the Firebase API key in frontend env vars or Cloudflare env vars.

- TTS unavailable
  The backend may be running without the required OpenAI credentials.
