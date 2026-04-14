---
title: YogaPoseFusion Backend
emoji: "🧘"
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
short_description: Yoga pose classification backend.
---

# YogaPoseFusion

YogaPoseFusion is a yoga coaching project that combines:

- pose classification from body landmarks
- personalized yoga routine recommendations
- real-time posture correction
- a React frontend for guided practice
- a FastAPI backend for inference, recommendations, and live coaching APIs

The current repository contains the production web app and backend. Older unfinished mobile work and research-paper scaffolding have been removed from the active codebase.

## What The Project Does

The system is designed to help a user:

1. create a wellness profile based on age, experience, goals, and health factors
2. generate a ranked yoga routine from the Yoga-82 pose catalog
3. practice a selected pose with live coaching
4. receive feedback about pose alignment, confidence, and corrections

At a high level:

- the backend extracts pose landmarks and derived spectral features
- an ensemble of trained PyTorch models predicts the pose
- pose-specific rule logic generates correction guidance
- the frontend lets users log in, create a profile, generate a routine, and open the live coach

## Current Architecture

### Backend

The backend lives in [`backend/`](/Volumes/Dev/Project2/YogaPoseFusion/backend) and is built with FastAPI.

Main responsibilities:

- load the trained pose-classification ensemble
- expose health and catalog endpoints
- generate personalized recommendations
- accept image or webcam frame uploads
- provide real-time and session-based coaching responses
- expose text-to-speech support when OpenAI credentials are configured

Core backend files:

- [`backend/inference.py`](/Volumes/Dev/Project2/YogaPoseFusion/backend/inference.py): main FastAPI app and inference pipeline
- [`backend/models/recommendations.py`](/Volumes/Dev/Project2/YogaPoseFusion/backend/models/recommendations.py): recommendation logic and pose catalog helpers
- [`backend/models/pose_correction.py`](/Volumes/Dev/Project2/YogaPoseFusion/backend/models/pose_correction.py): pose-aware correction rules
- [`backend/models/frame_quality.py`](/Volumes/Dev/Project2/YogaPoseFusion/backend/models/frame_quality.py): framing and quality heuristics
- [`backend/models/personalization.py`](/Volumes/Dev/Project2/YogaPoseFusion/backend/models/personalization.py): profile storage and calibration helpers
- [`backend/models/pose_graph_spectral.py`](/Volumes/Dev/Project2/YogaPoseFusion/backend/models/pose_graph_spectral.py): spectral feature extraction

Model assets:

- `backend/models/pose_classifier_v4_fold1.pt` to `fold5.pt`
- `backend/models/scaler.pkl`

### Frontend

The active frontend lives in [`yoga-pose-fusion-frontend/`](/Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend).

It is a Create React App project that provides:

- login and registration with local form-based auth
- Google sign-in through Firebase Auth
- profile intake for user wellness and practice preferences
- recommendation generation UI
- live coaching workflow
- backend URL configuration for local or deployed usage

Important frontend files:

- [`yoga-pose-fusion-frontend/src/App.js`](/Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend/src/App.js): main app shell and authentication flow
- [`yoga-pose-fusion-frontend/src/PoseClassifier.js`](/Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend/src/PoseClassifier.js): live coaching UI
- [`yoga-pose-fusion-frontend/src/services/api.js`](/Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend/src/services/api.js): frontend API client
- [`yoga-pose-fusion-frontend/src/firebase.js`](/Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend/src/firebase.js): Firebase Google auth wiring

## Repository Structure

```text
YogaPoseFusion/
├── backend/                     FastAPI backend and model assets
├── docs/                        setup, API, demo, and deployment notes
├── requirements/                supporting requirements files
├── scripts/                     notebooks and helper scripts used during development
├── yoga-pose-fusion-frontend/   active React frontend
├── Dockerfile                   Docker build for backend deployment
└── README.md                    project overview
```

## Main Features

- Yoga pose classification from webcam/image pose landmarks
- Personalized routine generation using:
  - age
  - experience level
  - session duration
  - goals
  - health factors
- Live coaching with:
  - pose classification
  - corrective feedback
  - session reset support
  - optional WebSocket-based realtime flow
- Pose catalog and guided recommendations
- Firebase Google sign-in on the frontend
- Optional text-to-speech voice guidance through OpenAI-compatible TTS config

## Local Development

### Backend

Create a Python environment, install dependencies, and start FastAPI from the backend folder.

Typical local flow:

```bash
cd /Volumes/Dev/Project2/YogaPoseFusion/backend
pip install -r requirements.txt
uvicorn inference:app --host 0.0.0.0 --port 8000
```

Local backend URL:

```text
http://localhost:8000
```

### Frontend

Run the React app from the frontend folder:

```bash
cd /Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend
npm install
npm start
```

The frontend reads the backend URL from:

- `REACT_APP_API_BASE_URL`

The sample env file is:

- [`yoga-pose-fusion-frontend/.env.example`](/Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend/.env.example)

For local development, that value is usually:

```text
REACT_APP_API_BASE_URL=http://localhost:8000
```

## Firebase Auth Setup

The frontend supports Google authentication through Firebase.

Required frontend environment variables:

- `REACT_APP_FIREBASE_API_KEY`
- `REACT_APP_FIREBASE_AUTH_DOMAIN`
- `REACT_APP_FIREBASE_PROJECT_ID`
- `REACT_APP_FIREBASE_STORAGE_BUCKET`
- `REACT_APP_FIREBASE_MESSAGING_SENDER_ID`
- `REACT_APP_FIREBASE_APP_ID`

Firebase notes:

- enable `Google` under Firebase Authentication
- add your Cloudflare Pages domain under `Authentication -> Settings -> Authorized domains`

## API And Docs

Additional project documentation:

- [`docs/README.md`](/Volumes/Dev/Project2/YogaPoseFusion/docs/README.md)
- [`docs/API_DOCUMENTATION.md`](/Volumes/Dev/Project2/YogaPoseFusion/docs/API_DOCUMENTATION.md)
- [`docs/SETUP_GUIDE.md`](/Volumes/Dev/Project2/YogaPoseFusion/docs/SETUP_GUIDE.md)
- [`docs/DEMO_CHECKLIST.md`](/Volumes/Dev/Project2/YogaPoseFusion/docs/DEMO_CHECKLIST.md)
- [`docs/DEPLOY_HUGGINGFACE_CLOUDFLARE.md`](/Volumes/Dev/Project2/YogaPoseFusion/docs/DEPLOY_HUGGINGFACE_CLOUDFLARE.md)

## Deployment

### Current Direction

The project is now set up around:

- Backend: Hugging Face Docker Space
- Frontend: Cloudflare Pages

### Backend Deployment

The root [`Dockerfile`](/Volumes/Dev/Project2/YogaPoseFusion/Dockerfile) supports backend deployment as a Hugging Face Docker Space.

Important details:

- Space SDK: `Docker`
- Port: `7860`
- root README front matter is compatible with Space metadata

### Frontend Deployment

Cloudflare Pages should use:

- Framework preset: `React Static`
- Root directory: `yoga-pose-fusion-frontend`
- Build command: `npm run build`
- Build output directory: `build`

Important production environment variables:

- `REACT_APP_API_BASE_URL`
- `REACT_APP_FIREBASE_API_KEY`
- `REACT_APP_FIREBASE_AUTH_DOMAIN`
- `REACT_APP_FIREBASE_PROJECT_ID`
- `REACT_APP_FIREBASE_STORAGE_BUCKET`
- `REACT_APP_FIREBASE_MESSAGING_SENDER_ID`
- `REACT_APP_FIREBASE_APP_ID`
- `NODE_VERSION=22`

## Known Practical Notes

- The backend currently allows broad CORS and can be tightened later for the production frontend domain.
- Text-to-speech support may show as unavailable until the required OpenAI environment variables are configured in the backend deployment.
- Some training and experimentation artifacts still exist under `scripts/`, but they are not required for the deployed web product.
- Local form-based auth in the frontend is convenience auth only; Google sign-in is the stronger user-facing option.

## Status

The repository is now focused on the working web stack:

- FastAPI backend
- PyTorch pose ensemble
- React frontend
- Cloudflare Pages frontend deployment
- Hugging Face backend deployment
- Firebase Google authentication

If you want to explore the product quickly, start with:

1. backend local run or deployed backend URL
2. frontend setup in `yoga-pose-fusion-frontend/`
3. recommendation flow
4. live coach flow
