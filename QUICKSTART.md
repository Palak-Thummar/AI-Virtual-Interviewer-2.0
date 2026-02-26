# Quick Start Guide

Get the AI Virtual Interviewer platform running in 5 minutes!

## 🚀 Fastest Path: Using Docker

### Prerequisites
- Docker Desktop installed [https://www.docker.com/get-started](https://www.docker.com/get-started)
- Gemini API key [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

### Steps

1. **Clone and navigate to project:**
```bash
cd "c:\Users\Urwil\OneDrive\Desktop\AI interviewer"
```

2. **Create `.env` file:**
```bash
echo GEMINI_API_KEY=your-api-key-here > .env
echo SECRET_KEY=your-secret-key-here >> .env
echo DEBUG=False >> .env
```

On Windows PowerShell:
```powershell
@"
GEMINI_API_KEY=your-api-key-here
SECRET_KEY=your-secret-key-here
DEBUG=False
"@ | Out-File -Encoding UTF8 .env
```

3. **Start all services:**
```bash
docker-compose up -d
```

4. **Wait for services to be ready** (30-60 seconds):
```bash
docker-compose logs
```

5. **Done!** Open your browser:
   - 🎯 Frontend: http://localhost:3000
   - 📚 API Docs: http://localhost:8000/docs
   - 🗄️ MongoDB: localhost:27017 (admin:password123)

---

## Local Development: Without Docker

### Prerequisites
- Python 3.8+ 
- Node.js 16+
- MongoDB running locally

### Backend Setup (Terminal 1)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your Gemini API key

# Run server (port 8000)
python -m uvicorn app.main:app --reload
```

### Frontend Setup (Terminal 2)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run dev server (port 5173)
npm run dev
```

### Access the App

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## First Time Setup

### Step 1: Register an Account

1. Go to http://localhost:5173 (Frontend) or http://localhost:3000 (Docker)
2. Click "Register"
3. Fill in: Name, Email, Password
4. Click "Register"

### Step 2: Create a Test Interview

1. Click "Dashboard"
2. Click "Start New Interview"
3. Follow the 3-step setup wizard...

#### Step 2a: Upload Resume
- Download a sample resume or use your own
- Must be PDF or DOCX format
- Click "Upload Resume"

#### Step 2b: Enter Job Details
- **Job Role**: e.g., "Senior Backend Engineer"
- **Domain**: Select from dropdown
- **Job Description**: Paste from a real job posting
- **Number of Questions**: 3-5 (for testing)
- Click "Next"

#### Step 2c: Review & Start
- Review the Resume Match Analysis preview
- Click "Start Interview"

### Step 3: Complete Interview

1. **Answer Questions**: 
   - Read each question
   - Type your answer in the text area
   - You have 2 minutes per question
   - Click "Submit" or wait for timer

2. **View Results**:
   - See your overall score
   - Review **Resume Match Analysis** (THE KEY FEATURE!)
   - See improvement suggestions
   - Check question performance

---

## Common Tasks

### Check Backend Logs
```bash
# Docker
docker-compose logs backend -f

# Local
# Terminal will show output automatically
```

### Check Frontend Logs
```bash
# Docker
docker-compose logs frontend -f

# Local
# Check browser console: F12 → Console tab
```

### Reset Everything
```bash
# Docker
docker-compose down -v
docker-compose up -d

# Local
# Stop both terminals (Ctrl+C)
# Delete backend/uploads/* files
# Clear browser cache
# Restart both servers
```

### Access Database

```bash
# Docker with MongoDB CLI
docker-compose exec mongodb mongosh -u admin -p password123

# Commands:
# use ai_interviewer
# db.users.find()
# db.resumes.find()
# db.interviews.find()
# exit
```

### View API Requests

1. Open browser DevTools (F12)
2. Go to "Network" tab
3. Make API calls (register, login, etc.)
4. Click request to see details
5. Check "Response" tab for data

---

## Integration Checklist

- [ ] Frontend loads without errors (F12 Console)
- [ ] Can register a new account
- [ ] Can login with created account
- [ ] Can upload a resume
- [ ] Resume parsing shows text preview
- [ ] Can create interview with job description
- [ ] Resume analysis shows (ATS score, matched skills, etc.)
- [ ] Interview session timer works
- [ ] Can submit answers
- [ ] Results page shows score
- [ ] Resume match analysis displays
- [ ] Suggestions are visible

---

## Troubleshooting

### "Cannot reach backend" error
```bash
# Check if backend is running
curl http://localhost:8000/health

# Docker:
docker-compose ps
docker-compose logs backend

# Local:
# Make sure you ran: python -m uvicorn app.main:app --reload
```

### "Gemini API error"
```bash
# Check API key is correct in .env
cat .env | grep GEMINI_API_KEY

# Get new key: https://makersuite.google.com/app/apikey
```

### "File upload fails"
```bash
# Check file is PDF or DOCX
# Check file size < 10MB
# Verify backend has write permissions to uploads/ directory
```

### "MongoDB connection error"
```bash
# Docker: wait 30 seconds for MongoDB to start
docker-compose logs mongodb

# Local: ensure MongoDB is running
# Windows: Services → MongoDB → Start
# macOS: brew services start mongodb-community
```

### "Port already in use"
```bash
# Docker: edit docker-compose.yml, change port mapping
# ports:
#   - "8001:8000"  # Use 8001 instead of 8000

# Local: kill process using port
# Windows: netstat -ano | findstr :8000
# macOS/Linux: lsof -i :8000
```

---

## Environment Variables

### Required
- `GEMINI_API_KEY`: Get from https://makersuite.google.com/app/apikey

### Optional (Defaults provided)
- `SECRET_KEY`: JWT secret (auto-generated)
- `DEBUG`: Set to `True` for development
- `MONGODB_URL`: MongoDB connection string
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT expiration time

---

## Project Structure Quick Reference

```
backend/           → Python FastAPI server
├── app/
│   ├── api/        → API endpoints
│   ├── services/   → AI services (resume analysis, question generation, etc.)
│   ├── models/     → Database models
│   └── core/       → Config, security, database

frontend/          → React + Vite web app
├── src/
│   ├── pages/      → App pages (Login, Interview, Results, etc.)
│   ├── components/ → Reusable UI components
│   ├── context/    → State management (Auth, Interview)
│   └── services/   → API client
```

---

## Useful Commands

### Docker Commands
```bash
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose logs -f            # View all logs
docker-compose ps                 # Check status
docker-compose restart backend    # Restart specific service
docker-compose build --no-cache   # Rebuild without cache
```

### Backend Commands (Local)
```bash
python -m venv venv               # Create environment
source venv/bin/activate          # Activate (macOS/Linux)
venv\Scripts\activate             # Activate (Windows)
pip install -r requirements.txt   # Install dependencies
python -m uvicorn app.main:app --reload   # Run server
```

### Frontend Commands (Local)
```bash
npm install                       # Install dependencies
npm run dev                       # Start dev server
npm run build                     # Build for production
npm run preview                   # Preview production build
```

---

## Next Steps

### Go Beyond Quick Start
- Read detailed [Backend README](./backend/README.md)
- Read detailed [Frontend README](./frontend/README.md)
- Check [API Documentation](./API.md)
- Review [Docker Setup](./DOCKER.md)

### Advanced Setup
- Configure production environment
- Set up CI/CD pipeline
- Deploy to AWS/GCP/Azure
- Add more features

### Testing
- Create multiple test interviews
- Try different job roles and domains
- Test resume parsing with different formats
- Verify all calculations and scores

---

## Support Resources

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **GitHub Issues**: Create issue for bugs
- **Email**: support@aiinterviewer.com

---

## 🎉 You're All Set!

The platform is now ready to use. Start with a test interview to see how it works, then use real resume and job descriptions to prepare for actual interviews!

**Happy interviewing! 🚀**

---

### Quick Command Reference Card

```
Starting:
  docker-compose up -d          (recommended)
  npm run dev && python...      (alternative)

Accessing:
  Frontend:  http://localhost:3000 (Docker)
             http://localhost:5173 (Local)
  Backend:   http://localhost:8000
  Docs:      http://localhost:8000/docs

Stopping:
  docker-compose down
  Ctrl+C in both terminals

Debugging:
  docker-compose logs -f
  Browser console (F12)
  Network tab in DevTools
```
