# Deploy YogaPoseFusion

This project is set up to deploy with:

- Backend: Render Web Service
- Frontend: Cloudflare Pages

## Architecture

- `backend/` runs the FastAPI inference API.
- `yoga-pose-fusion-frontend/` builds the React app.
- The frontend talks to the backend through `REACT_APP_API_BASE_URL`.

## 1. Push the repository

Push this repository to GitHub before deploying.

## 2. Deploy the backend on Render

This repo includes [render.yaml](/Volumes/Dev/Project2/YogaPoseFusion/render.yaml:1), so Render can create the backend service from the repo.

### Option A: Blueprint

1. In Render, choose `New +` -> `Blueprint`.
2. Select your GitHub repository.
3. Render will detect `render.yaml`.
4. Create the service.

### Backend dependency files

- Local development: `backend/requirements.txt`
- Container and cloud deployment: `backend/requirements-deploy.txt`

The deploy file is pinned more tightly for Linux compatibility and stable deploys.

### Option B: Manual Web Service

If you prefer manual setup, use:

- Root directory: `backend`
- Environment: `Python`
- Build command: `pip install -r requirements-deploy.txt`
- Start command: `uvicorn inference:app --host 0.0.0.0 --port $PORT`

### Notes

- Plan: `Free`
- Health check path: `/`
- Keep the default public URL, for example:
  `https://yogaposefusion-api.onrender.com`

## 3. Deploy the frontend on Cloudflare Pages

Create a new Pages project from the same GitHub repository with these settings:

- Framework preset: `Create React App`
- Root directory: `yoga-pose-fusion-frontend`
- Build command: `npm install && npm run build`
- Build output directory: `build`

### Environment variable

Add this production variable in Cloudflare Pages:

- Key: `REACT_APP_API_BASE_URL`
- Value: your Render backend URL, for example:
  `https://yogaposefusion-api.onrender.com`

The frontend reads this value from [App.js](/Volumes/Dev/Project2/YogaPoseFusion/yoga-pose-fusion-frontend/src/App.js:12).

## 4. Redeploy the frontend

After adding `REACT_APP_API_BASE_URL`, trigger a new Cloudflare Pages deploy so the React build picks up the backend URL.

## 5. Verify

After both deploys are live:

1. Open the Cloudflare Pages site.
2. Go to the app settings tab.
3. Confirm the backend URL is not `localhost`.
4. Generate recommendations.
5. Open Live Coach and confirm the API status is online.
6. Confirm pose catalog and reference images load.

## 6. Important free-tier caveats

- Render free services spin down after inactivity.
- The first API request after sleeping may take around a minute.
- Large ML dependencies can make the first build slow.
- If webcam access is blocked, confirm browser permissions and HTTPS are enabled on the deployed Pages site.

## 7. Optional cleanup for production

Later, you may want to:

- Replace `allow_origins=["*"]` in the backend CORS config with your Cloudflare Pages domain.
- Move heavy model assets to external storage if Render build size becomes an issue.
- Add a custom domain to Cloudflare Pages.

## 8. Hugging Face Docker Space backend

If Render free runs out of memory, this repo can also be deployed as a Hugging Face Docker Space.

- Space SDK: `Docker`
- Docker file: repo root `Dockerfile`
- Space config: repo root `README.md`
- Port: `7860`

The Docker build only copies the backend runtime files and excludes the large training dataset through [.dockerignore](/Volumes/Dev/Project2/YogaPoseFusion/.dockerignore:1).
