# Docs Overview

This folder contains the current working documentation for YogaPoseFusion.

## Files

- `API_DOCUMENTATION.md`
  Explains the backend endpoints exposed by `backend/inference.py`.

- `SETUP_GUIDE.md`
  Local development setup for the FastAPI backend and React frontend.

- `DEMO_CHECKLIST.md`
  A practical checklist for testing or presenting the app end-to-end.

- `DEPLOY_HUGGINGFACE_CLOUDFLARE.md`
  Production deployment flow for:
  - Hugging Face Docker Space backend
  - Cloudflare Pages frontend
  - Firebase Google authentication

## Current Stack

- Backend: FastAPI + MediaPipe + PyTorch ensemble
- Frontend: Create React App
- Auth: Local form-based auth plus Firebase Google sign-in
- Backend hosting: Hugging Face Docker Space
- Frontend hosting: Cloudflare Pages

## Recommended Reading Order

1. `SETUP_GUIDE.md`
2. `API_DOCUMENTATION.md`
3. `DEMO_CHECKLIST.md`
4. `DEPLOY_HUGGINGFACE_CLOUDFLARE.md`
