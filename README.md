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

An AI-assisted yoga coaching platform that combines pose recognition, personalized practice planning, and real-time correction in a single web experience.

[Live Website](https://yogaposefusion.pages.dev) | [Docs](./docs/README.md) | [Deployment Guide](./docs/DEPLOY_HUGGINGFACE_CLOUDFLARE.md)

## Why This Project Exists

YogaPoseFusion is built for self-guided practice. Instead of giving every user the same routine, it tries to adapt the session to the person and then help them execute the selected pose more accurately.

The core idea is:

1. understand the user profile
2. recommend poses that fit the user’s goals and health factors
3. analyze the performed pose from visual landmarks
4. return alignment-aware feedback in real time

## What It Includes

### Personalized Practice Planning

- age-aware and experience-aware routine generation
- goal-based and health-factor-aware ranking
- guided pose selection from the Yoga-82 pose library
- routine summaries, hold durations, repetitions, and coaching notes

### Real-Time Coaching

- pose classification from image or webcam frames
- correction rules based on landmark geometry and pose-aware heuristics
- feedback for low-confidence or poor-framing conditions
- REST and WebSocket-based live coaching modes
- optional voice synthesis support when backend TTS is configured

### Web Product Experience

- React-based guided practice interface
- local form-based login/register flow
- Firebase Google sign-in
- live coach interface with backend connectivity
- deployment-ready frontend on Cloudflare Pages

## Live Project

Production frontend:

- [https://yogaposefusion.pages.dev](https://yogaposefusion.pages.dev)

Current production architecture:

- Frontend: Cloudflare Pages
- Backend: Hugging Face Docker Space
- Auth: Firebase Google sign-in plus local form-based auth in the UI

## Architecture Overview

### Backend

The backend is a FastAPI service located in [`backend/`](/Volumes/Dev/Project2/YogaPoseFusion/backend).

It is responsible for:

- loading the PyTorch ensemble checkpoints
- extracting and transforming pose features
- serving the guided pose catalog
- generating recommendation plans
- running single-frame and realtime coaching inference
- exposing optional text-to-speech output

Key backend files:

- [`backend/inference.py`](/Volumes/Dev/Project2/YogaPoseFusion/backend/inference.py)
- [`backend/models/recommendations.py`](/Volumes/Dev/Project2/YogaPoseFusion/backend/models/recommendations.py)
- [`backend/models/pose_correction.py`](/Volumes/Dev/Project2/YogaPoseFusion/backend/models/pose_correction.py)
- [`backend/models/frame_quality.py`](/Volumes/Dev/Project2/YogaPoseFusion/backend/models/frame_quality.py)
- [`backend/models/personalization.py`](/Volumes/Dev/Project2/YogaPoseFusion/backend/models/personalization.py)
- [`backend/models/pose_graph_spectral.py`](/Volumes/Dev/Project2/YogaPoseFusion/backend/models/pose_graph_spectral.py)

Model assets:

- `backend/models/pose_classifier_v4_fold1.pt` to `backend/models/pose_classifier_v4_fold5.pt`
- `backend/models/scaler.pkl`

### Frontend

The active frontend is in [`yoga-pose-fusion-frontend/`](/Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend).

It handles:

- authentication UI
- recommendation generation flow
- live practice UX
- backend status and API integration
- Firebase Google auth wiring

Key frontend files:

- [`yoga-pose-fusion-frontend/src/App.js`](/Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend/src/App.js)
- [`yoga-pose-fusion-frontend/src/PoseClassifier.js`](/Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend/src/PoseClassifier.js)
- [`yoga-pose-fusion-frontend/src/services/api.js`](/Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend/src/services/api.js)
- [`yoga-pose-fusion-frontend/src/firebase.js`](/Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend/src/firebase.js)

## Repository Structure

```text
YogaPoseFusion/
├── backend/                     FastAPI backend, model files, recommendation logic
├── docs/                        project documentation
├── requirements/                supporting requirements files
├── scripts/                     notebooks and helper experimentation scripts
├── yoga-pose-fusion-frontend/   active React frontend
├── Dockerfile                   backend deployment image for Hugging Face Spaces
└── README.md                    repository overview
```

## Core Features

- Pose classification from landmark-driven features
- Personalized recommendation generation
- Guided pose library and routine selection
- Realtime feedback and correction
- Session-level coaching flow
- Firebase Google sign-in support
- Cloud-ready deployment setup for frontend and backend

## Local Development

### Run The Backend

```bash
cd /Volumes/Dev/Project2/YogaPoseFusion/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn inference:app --host 0.0.0.0 --port 8000 --reload
```

Backend URL:

```text
http://localhost:8000
```

### Run The Frontend

```bash
cd /Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend
npm install
npm start
```

Frontend URL:

```text
http://localhost:3000
```

## Environment Variables

### Frontend

The frontend uses:

- `REACT_APP_API_BASE_URL`
- `REACT_APP_FIREBASE_API_KEY`
- `REACT_APP_FIREBASE_AUTH_DOMAIN`
- `REACT_APP_FIREBASE_PROJECT_ID`
- `REACT_APP_FIREBASE_STORAGE_BUCKET`
- `REACT_APP_FIREBASE_MESSAGING_SENDER_ID`
- `REACT_APP_FIREBASE_APP_ID`

Reference file:

- [`yoga-pose-fusion-frontend/.env.example`](/Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend/.env.example)

### Backend

The backend can optionally use environment variables for TTS-related features. If those are missing, core pose analysis and recommendation flows still work.

## Documentation

Project docs live in [`docs/`](/Volumes/Dev/Project2/YogaPoseFusion/docs).

Start here:

- [`docs/README.md`](/Volumes/Dev/Project2/YogaPoseFusion/docs/README.md)
- [`docs/SETUP_GUIDE.md`](/Volumes/Dev/Project2/YogaPoseFusion/docs/SETUP_GUIDE.md)
- [`docs/API_DOCUMENTATION.md`](/Volumes/Dev/Project2/YogaPoseFusion/docs/API_DOCUMENTATION.md)
- [`docs/DEMO_CHECKLIST.md`](/Volumes/Dev/Project2/YogaPoseFusion/docs/DEMO_CHECKLIST.md)
- [`docs/DEPLOY_HUGGINGFACE_CLOUDFLARE.md`](/Volumes/Dev/Project2/YogaPoseFusion/docs/DEPLOY_HUGGINGFACE_CLOUDFLARE.md)

## Deployment

### Backend

The backend is prepared for Hugging Face Docker Spaces using:

- [`Dockerfile`](/Volumes/Dev/Project2/YogaPoseFusion/Dockerfile)
- [`.dockerignore`](/Volumes/Dev/Project2/YogaPoseFusion/.dockerignore)
- the Space metadata in this root README

### Frontend

The frontend is deployed on Cloudflare Pages with:

- root directory: `yoga-pose-fusion-frontend`
- framework preset: `React Static`
- build command: `npm run build`
- output directory: `build`

## Current Status

The repository is now focused on the active web product only:

- web frontend
- FastAPI backend
- pose recommendation and live coaching flow
- Firebase-backed Google sign-in
- Hugging Face + Cloudflare deployment path

Older abandoned mobile work and paper-specific repository clutter have been removed so the project reflects the current product direction more clearly.
