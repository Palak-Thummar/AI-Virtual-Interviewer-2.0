# Quick Deployment Guide (First-Time Friendly)

Use this exact sequence for fastest production deployment.

## 1) Backend on Render (Web Service)

- Service Type: `Web Service`
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Backend Environment Variables (Render)

Set these in Render → Environment:

- `PYTHON_VERSION=3.12.8`
- `APP_NAME=AI Virtual Interviewer`
- `APP_VERSION=1.0.0`
- `DEBUG=False`
- `MONGODB_URL=<your-mongodb-url>`
- `MONGODB_DB=ai_interviewer`
- `SECRET_KEY=<strong-random-secret>`
- `ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=30`
- `OPENROUTER_API_KEY=<your-openrouter-key>`
- `OPENROUTER_MODEL_NAME=nvidia/nemotron-3-nano-30b-a3b:free`
- `UPLOAD_DIR=./uploads`
- `MAX_FILE_SIZE=10485760`
- `CORS_ORIGINS=<set after frontend deploy>`

### Backend Health Check

After deploy, open:

- `https://<backend-url>/health`

Expected: JSON with `status: healthy`.

## 2) Frontend on Vercel

- Framework: `Vite`
- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `dist`

### Frontend Environment Variables (Vercel)

- `VITE_API_SERVER_URL=https://<backend-url>`

Important: do not append `/api` in this value.

## 3) Final CORS Wiring

After frontend URL is created, set backend `CORS_ORIGINS` in Render to:

`https://<your-vercel-url>,http://localhost:5173,http://127.0.0.1:5173`

Then redeploy backend.

## 4) Smoke Test

- Register/Login
- Open Settings and save profile/preferences
- Create and complete one interview
- Open Career Intelligence and Interview History
- Upload resume in Settings

## 5) Common Deployment Errors

- `gunicorn your_application.wsgi`: wrong start command (Django default)
  - fix to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- `email-validator is not installed`
  - fixed by `email-validator` in `backend/requirements.txt`
- pydantic-core / Rust build issues
  - force Python `3.12.8`

## 6) Security Reminder

If secrets were ever exposed during setup logs/chat:

- Rotate MongoDB password
- Rotate OpenRouter API key
- Update Render env values
