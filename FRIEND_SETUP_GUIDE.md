# Friend Setup Guide (Windows)

This guide helps you clone and run the AI Placement Preparation Platform exactly like it runs on this device.

## 1) Prerequisites

Install these first:

- Git
- Python 3.12+
- Node.js 18+
- MongoDB (local service or MongoDB Atlas URL)

Optional but recommended:

- VS Code
- MongoDB Compass

## 2) Clone Repository

Open CMD or PowerShell and run:

```bash
git clone <YOUR_GITHUB_REPO_URL>
cd <YOUR_REPO_FOLDER_NAME>
```

## 3) Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Now open `.env` and set real values:

- `MONGODB_URL`
- `MONGODB_DB`
- `SECRET_KEY`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL_NAME`
- `CORS_ORIGINS`

Start backend:

```bash
python -m uvicorn app.main:app --reload
```

Backend should run at:

- `http://127.0.0.1:8000`

Keep this terminal open.

## 4) Frontend Setup

Open a second terminal:

```bash
cd <YOUR_REPO_FOLDER_NAME>\frontend
npm install
npm run dev
```

Frontend should run at:

- `http://127.0.0.1:5173`

## 5) First Run Checklist

- Open `http://127.0.0.1:5173`
- Register a new user
- Login
- Open Settings and save preferences once
- Start an interview and complete it

## 6) Daily Run (After First Setup)

Fastest option (recommended):

```bash
start-dev.bat
```

This opens two terminals automatically (backend + frontend).

Manual option:

Terminal 1:

```bash
cd <YOUR_REPO_FOLDER_NAME>\backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

Terminal 2:

```bash
cd <YOUR_REPO_FOLDER_NAME>\frontend
npm run dev
```

## 7) Common Issues

### Backend does not start

- Confirm virtual environment is active (`venv\Scripts\activate`)
- Confirm `.env` exists in `backend`
- Confirm MongoDB URL is valid

### Frontend cannot call API

- Confirm backend is running on port `8000`
- Confirm frontend runs on `5173`
- Confirm `CORS_ORIGINS` includes `http://localhost:5173` and `http://127.0.0.1:5173`

### Module not found / dependency errors

- Backend: run `pip install -r requirements.txt`
- Frontend: run `npm install`

## 8) Optional: Production Build Check

Frontend:

```bash
cd frontend
npm run build
```

Backend quick syntax check:

```bash
cd backend
python -m py_compile app/main.py
```
