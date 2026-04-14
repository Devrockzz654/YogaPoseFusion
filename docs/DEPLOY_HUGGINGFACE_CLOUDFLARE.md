# Deploy YogaPoseFusion

This project is currently set up to deploy with:

- Backend: Hugging Face Docker Space
- Frontend: Cloudflare Pages

## Architecture

- `backend/` runs the FastAPI inference API.
- `yoga-pose-fusion-frontend/` builds the React app.
- The frontend talks to the backend through `REACT_APP_API_BASE_URL`.

## 1. Push the repository

Push the repository to GitHub before deploying the frontend on Cloudflare Pages.

## 2. Deploy the backend on Hugging Face Spaces

Create a new Hugging Face Space with these settings:

- Space type: `Docker`
- Repository: your YogaPoseFusion backend repo
- Port: `7860`

This repository already includes:

- [`Dockerfile`](/Volumes/Dev/Project2/YogaPoseFusion/Dockerfile)
- root [`README.md`](/Volumes/Dev/Project2/YogaPoseFusion/README.md) with Space metadata
- [`.dockerignore`](/Volumes/Dev/Project2/YogaPoseFusion/.dockerignore)

### Backend dependency files

- Local development: `backend/requirements.txt`
- Deployment/runtime install: `backend/requirements-deploy.txt`

### Verify the backend

Once the Space starts:

1. open the Space app URL
2. open `/docs` if exposed
3. confirm the API root returns a healthy status payload
4. verify that model loading succeeds

## 3. Deploy the frontend on Cloudflare Pages

Create a new Cloudflare Pages project from the same GitHub repository with these settings:

- Framework preset: `React Static`
- Root directory: `yoga-pose-fusion-frontend`
- Build command: `npm run build`
- Build output directory: `build`

## 4. Required Cloudflare environment variables

Set these production variables in Cloudflare Pages:

### Backend URL

- `REACT_APP_API_BASE_URL`
- value: your Hugging Face backend URL, for example:
  `https://sudebkumar012-yogaposefusion-backend.hf.space`

### Firebase Auth

- `REACT_APP_FIREBASE_API_KEY`
- `REACT_APP_FIREBASE_AUTH_DOMAIN`
- `REACT_APP_FIREBASE_PROJECT_ID`
- `REACT_APP_FIREBASE_STORAGE_BUCKET`
- `REACT_APP_FIREBASE_MESSAGING_SENDER_ID`
- `REACT_APP_FIREBASE_APP_ID`
- `NODE_VERSION=22`

## 5. Firebase production setup

In Firebase Authentication:

1. enable `Google` as a sign-in provider
2. go to `Authentication -> Settings -> Authorized domains`
3. add your Cloudflare Pages production domain

For example:

- `yogaposefusion.pages.dev`

## 6. Redeploy the frontend

After updating Cloudflare environment variables, trigger a redeploy so the frontend build picks up the latest backend and Firebase config.

## 7. Verify the full app

After both backend and frontend are live:

1. open the Cloudflare Pages site
2. verify the login/register panel loads
3. test local form-based login/register
4. test Google sign-in
5. generate recommendations
6. open Live Coach
7. confirm backend status, pose catalog, and realtime endpoints work

## 8. Practical notes

- If Google sign-in fails with domain-related errors, add the active Pages domain to Firebase Authorized Domains.
- If Google sign-in fails with `auth/api-key-not-valid`, re-check the Firebase API key in Cloudflare.
- If TTS is unavailable, configure the required OpenAI environment variables in the backend deployment.
- You may later tighten backend CORS to only allow your production frontend domain.
