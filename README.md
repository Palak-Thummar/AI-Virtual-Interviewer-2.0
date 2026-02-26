    # AI Placement Preparation Platform

Production-ready full-stack platform for interview preparation with AI-powered interview generation, session evaluation, career intelligence, coding practice, answer lab, resume tools, and a modular settings system.

## Tech Stack

- Frontend: React + Vite, React Router v6, Zustand, Axios, Recharts, CSS Modules
- Backend: FastAPI, MongoDB, JWT auth, OpenRouter integration
- Resume parsing: pdfplumber, python-docx

## New Here?

Use the step-by-step Windows clone/run guide: [FRIEND_SETUP_GUIDE.md](FRIEND_SETUP_GUIDE.md)

## Repository Structure

- `backend/` - FastAPI server, API routes, services, and data logic
- `frontend/` - React app and UI modules
- `LICENSE` - MIT license
- `.gitignore` - GitHub-ready ignore rules

## Quick Start

## 1) Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload
```

Backend runs at: `http://127.0.0.1:8000`

## 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://127.0.0.1:5173`

## Quick Local Start (Windows)

After first-time setup, run this from repo root:

```bash
start-dev.bat
```

## Render Deploy Note (Important)

If Render build fails on `pydantic-core` / Rust during install, force Python `3.12.8`.

- This repo includes `backend/runtime.txt` and `backend/.python-version`.
- In Render service settings, also set env var: `PYTHON_VERSION=3.12.8`.

## Environment Configuration

Edit `backend/.env` from the template and set:

- `MONGODB_URL`
- `MONGODB_DB`
- `SECRET_KEY`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL_NAME`
- `CORS_ORIGINS`

## Core Modules

- Auth: `/api/auth/*`
- Interview: `/api/interview/*`
- Career Intelligence: `/api/career-intelligence`
- Analytics summary: `/api/analytics/summary`
- Settings (modular config layer): `/api/settings/*`
- Resume management: `/api/resume/*`
- Coding practice: `/api/coding/*`
- Answer lab: `/api/answer-lab/*`

## Settings Module (Independent)

The Settings module is isolated from analytics/interview pages and includes:

- Profile management
- Security / password change
- AI interview preferences
- Resume upload/replace/delete with skill extraction
- Notification controls
- Data export and hard account delete

Frontend route: `/settings`

## Tests

Backend tests (including settings/intelligence test files):

```bash
cd backend
pytest -q
```

## GitHub Publish Checklist

- `.env` files are ignored
- `node_modules`, `venv`, build outputs, uploads ignored
- `LICENSE` included
- `README.md` updated
- `backend/requirements.txt` includes runtime + test dependency (`pytest`)

## Suggested First Commit

```bash
git init
git add .
git commit -m "Initial commit: AI placement preparation platform"
```

Then create your GitHub repo and push:

```bash
git remote add origin <your-repo-url>
git branch -M main
git push -u origin main
```
