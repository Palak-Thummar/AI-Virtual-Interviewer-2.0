# AI Placement Preparation Platform

Production-ready full-stack platform for interview preparation with AI-powered interview generation, session evaluation, career intelligence, coding practice, answer lab, resume tools, and a modular settings system.

## Tech Stack

- Frontend: React + Vite, React Router v6, Zustand, Axios, Recharts, CSS Modules
- Backend: FastAPI, MongoDB, JWT auth, OpenRouter integration
- Resume parsing: pdfplumber, python-docx

## New Here?

Use the step-by-step Windows clone/run guide: [FRIEND_SETUP_GUIDE.md](FRIEND_SETUP_GUIDE.md)

For deployment setup: [DEPLOY_QUICK.md](DEPLOY_QUICK.md)

## Repository Structure

- `backend/` - FastAPI server, API routes, services, and data logic
- `frontend/` - React app and UI modules
- `LICENSE` - MIT license
- `.gitignore` - GitHub-ready ignore rules

## Quick Start

## 1) Backend

# CareerIQ — AI Virtual Interviewer

Production-ready SaaS platform for interview preparation. AI-powered mock interviews, adaptive question generation, real-time scoring with skill breakdown, career intelligence dashboard, coding practice, and a full onboarding flow.

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite 7, React Router v6, Zustand, Recharts, CSS Modules |
| **Backend** | FastAPI 0.104, Python 3.11+, Pydantic v2, Uvicorn |
| **Database** | MongoDB 7 (PyMongo 4.6) |
| **Auth** | JWT (PyJWT) + bcrypt (passlib) |
| **AI** | OpenRouter API (configurable model) |
| **Rate limiting** | slowapi (IP-based, in-memory) |
| **Deployment** | Docker + docker-compose / Render + Vercel |

---

## Features

- **Onboarding wizard** — 3-step signup flow (resume upload → role selection → first interview)
- **AI mock interviews** — per-question evaluation with overall score and detailed skill feedback
- **Career Intelligence** — persistent dashboard tracking skill trends, strongest/weakest areas, streaks, achievements, job-readiness index
- **Coding Practice** — code editor with Judge0 execution
- **Answer Lab** — refine past answers with AI coaching
- **Resume Rewriter** — AI-assisted resume bullet improvements
- **Company Prep** — company-specific interview sets
- **Settings** — profile, password, AI preferences, notification controls, data export
- **Rate limiting** — auth endpoints capped at 10 req/min per IP; global API at 60 req/min

---

## Repository Structure

```
├── backend/           FastAPI server
│   ├── app/
│   │   ├── api/       Routers + dependency injection
│   │   ├── core/      Config, DB, security, logging
│   │   ├── models/    MongoDB document shapes
│   │   ├── schemas/   Pydantic request/response schemas
│   │   ├── services/  AI evaluation, career intelligence, parsing
│   │   └── utils/
│   ├── test_production.py   Production test suite (34 tests)
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/          React + Vite SPA
│   ├── src/
│   │   ├── components/   Shared UI components
│   │   ├── context/      Auth context (JWT state)
│   │   ├── pages/        Route-level page components
│   │   ├── services/     Axios API client
│   │   └── store/        Zustand stores
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml  Full-stack local deployment
└── render.yaml         Render.com deployment config
```

---

## Local Development

### Prerequisites

- Python 3.11+ and `pip`
- Node.js 20+ and `npm`
- MongoDB 7 (local or [MongoDB Atlas](https://www.mongodb.com/atlas) free tier)
- [OpenRouter API key](https://openrouter.ai/)

### 1. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Configure environment
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux
# Edit .env with your values (see Environment Variables below)

# Run development server
uvicorn app.main:app --reload
```

Backend: **http://localhost:8000**  
API docs: **http://localhost:8000/docs**  
Health check: **http://localhost:8000/health**

### 2. Frontend

```bash
cd frontend
npm install

# Configure environment
copy .env.example .env.local   # Windows
cp .env.example .env.local     # macOS/Linux
# Set VITE_API_SERVER_URL=http://localhost:8000

npm run dev
```

Frontend: **http://localhost:5173**

### Windows — one-click start

After first-time setup, from the repo root:

```bat
start-dev.bat
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `MONGODB_URL` | ✅ | MongoDB connection string (`mongodb://...` or Atlas URI) |
| `MONGODB_DB` | ✅ | Database name (e.g. `careeriq`) |
| `SECRET_KEY` | ✅ | Random 32+ char string for JWT signing |
| `ALGORITHM` | | JWT algorithm — default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | | Token expiry — default `1440` (24 h) |
| `OPENROUTER_API_KEY` | ✅ | OpenRouter API key |
| `OPENROUTER_MODEL_NAME` | | Model — default `nvidia/nemotron-3-nano-30b-a3b:free` |
| `CORS_ORIGINS` | ✅ | Comma-separated allowed origins, e.g. `http://localhost:5173,https://yourapp.vercel.app` |
| `RATE_LIMIT_PER_MINUTE` | | Global API rate limit per IP — default `60` |
| `AUTH_RATE_LIMIT_PER_MINUTE` | | Auth endpoint rate limit — default `10` |
| `UPLOAD_DIR` | | Resume upload directory — default `uploads` |
| `MAX_FILE_SIZE` | | Max upload bytes — default `5242880` (5 MB) |
| `DEBUG` | | Set `true` to enable debug logging |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_SERVER_URL` | ✅ | Backend URL, e.g. `http://localhost:8000` or your Render URL |

---

## Docker Deployment (Full-stack)

The docker-compose setup includes MongoDB, backend, and frontend — all behind one command.

```bash
# Copy and fill in environment variables
cp backend/.env.example backend/.env
# Edit backend/.env

# Build and start all services
docker compose up --build
```

| Service | Port |
|---|---|
| Frontend (nginx) | http://localhost:3000 |
| Backend (uvicorn) | http://localhost:8000 |
| MongoDB | localhost:27017 |

Stop all services:

```bash
docker compose down
# To also delete the database volume:
docker compose down -v
```

---

## Cloud Deployment

### Backend → Render

1. Create a **Web Service** on [render.com](https://render.com)
2. Connect your GitHub repository, set **Root Directory** → `backend`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (all variables from the Backend table above)
6. Set `PYTHON_VERSION=3.11.9` in Render environment settings

> **Note:** If the build fails on `pydantic-core` (Rust compilation), the repo includes `backend/runtime.txt` set to `python-3.12.8` as a fallback — update it if needed.

7. Configure a free [MongoDB Atlas](https://www.mongodb.com/atlas) cluster and set `MONGODB_URL` to the Atlas connection string
8. Set `CORS_ORIGINS` to include your Vercel frontend URL

### Frontend → Vercel

1. Import your GitHub repository on [vercel.com](https://vercel.com)
2. Set **Framework Preset** → `Vite`
3. Set **Root Directory** → `frontend`
4. Add environment variable: `VITE_API_SERVER_URL` = your Render backend URL
5. Deploy — Vercel auto-builds on every push to `main`

The `frontend/vercel.json` includes the SPA rewrite rule (`/* → /index.html`) so client-side routing works correctly.

---

## Running Tests

```bash
# From the repo root (venv must be active)
python -m pytest backend/test_production.py -v

# Or from inside the backend directory
cd backend
pytest -v
```

**34 tests** covering:
- JWT token creation, decoding, tampering detection
- Password hashing and verification
- Register / login endpoint logic (success, duplicate email, wrong password, edge cases)
- Auth dependency (Bearer token extraction and validation)
- MongoDB index creation
- Career Intelligence aggregation (scores, skill breakdown, recommendations)
- Settings endpoint (preferences defaults, profile update)
- Health check endpoint

---

## API Overview

All endpoints return `{"success": true/false, ...}` shaped responses. Errors include an `"error"` string field.

### Auth (`/api/auth`)
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/register` | — | Register (10 req/min limit) |
| POST | `/login` | — | Login (10 req/min limit) |
| GET | `/me` | ✅ | Current user profile |
| POST | `/refresh` | ✅ | Refresh access token |
| PATCH | `/onboarding` | ✅ | Complete onboarding |
| GET | `/onboarding-status` | ✅ | Check onboarding state |

### Interview (`/api/interview`)
| POST | `/start` | ✅ | Create new interview session |
| GET | `/{id}` | ✅ | Get interview details |
| POST | `/{id}/answer` | ✅ | Submit answer, get AI evaluation |
| POST | `/{id}/skip` | ✅ | Skip current question |
| POST | `/{id}/complete` | ✅ | Finish interview |

### Other protected routes
- `/api/analytics/*` — summary stats
- `/api/career-intelligence` — full career dashboard data
- `/api/settings/*` — profile, password, preferences, notifications, resume
- `/api/resume/*` — upload, parse, list
- `/api/coding/*` — Judge0 code execution
- `/api/answer-lab/*` — answer analysis
- `/api/practice-center/*` — practice sets
- `/api/coach/*` — AI coaching feedback

---

## Security Notes

- Passwords are hashed with **bcrypt** (passlib, cost factor 12)
- JWTs are signed with HS256; the `SECRET_KEY` must be kept private
- Rate limiting is applied per client IP using **slowapi** (in-memory)
	- For high-traffic production, configure a Redis backend for `slowapi`
- File uploads validate MIME type and extension; max size 5 MB
- CORS is locked to explicitly configured origins (no wildcard in production)

---

## GitHub Publish Checklist

- [ ] `backend/.env` is in `.gitignore` (it is — never commit secrets)
- [ ] `node_modules/`, `venv/`, `dist/`, `uploads/` are ignored (they are)
- [ ] `LICENSE` included
- [ ] All environment variables documented in `.env.example`

```bash
git init
git add .
git commit -m "Initial commit: CareerIQ AI Virtual Interviewer"
git remote add origin <your-repo-url>
git branch -M main
git push -u origin main
```
