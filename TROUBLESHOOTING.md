# Troubleshooting & FAQ

## Common Issues & Solutions

### Backend Startup Issues

#### "ModuleNotFoundError: No module named 'app'"

**Problem:** Python can't find the app module

**Solutions:**
```bash
# 1. Ensure you're in the backend directory
cd backend

# 2. Check requirements.txt is installed
pip install -r requirements.txt

# 3. Verify Python path includes current directory
# Add current directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # macOS/Linux
set PYTHONPATH=%cd%  # Windows

# 4. Run from backend directory
python -m uvicorn app.main:app --reload
```

#### "Error: Failed to connect to MongoDB"

**Problem:** Backend can't reach MongoDB

**Solutions:**
```bash
# 1. Check MongoDB is running
mongosh --eval "db.adminCommand('ping')"

# 2. Verify MONGODB_URL in .env
cat .env | grep MONGODB_URL

# 3. Test connection string
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
print(client.admin.command('ping'))
"

# 4. For Docker:
docker-compose ps
docker-compose logs mongodb
```

If MongoDB is not installed:

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Windows:**
- Download installer: https://www.mongodb.com/try/download/community
- Run installer and follow wizard
- MongoDB should start automatically

**Linux (Ubuntu):**
```bash
wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
```

#### "Gemini API Key Error"

**Problem:** "Error 400: Invalid API Key" or similar

**Solutions:**
```bash
# 1. Verify API key is correct
cat .env | grep GEMINI_API_KEY
# Should not be empty or "your-key-here"

# 2. Get new API key
# Visit: https://makersuite.google.com/app/apikey
# Click "Create API Key"
# Copy and paste into .env

# 3. Test API key
python -c "
import google.generativeai as genai
genai.configure(api_key='YOUR_KEY')
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('Hello')
print(response.text)
"

# 4. Check API is enabled
# Go to Google Cloud Console
# Enable Generative Language API
```

---

### Frontend Issues

#### "Cannot GET / error"

**Problem:** Frontend won't load, shows blank page or error

**Solutions:**
```bash
# 1. Check frontend server is running
curl http://localhost:5173
# Should get HTML response

# 2. Restart npm dev server
npm run dev

# 3. Clear cache and rebuild
rm -rf node_modules dist
npm install
npm run dev

# 4. Check for port conflicts
# Windows:
netstat -ano | findstr :5173
# macOS/Linux:
lsof -i :5173
```

#### "API connection refused" error in browser

**Problem:** "Failed to fetch from API" or "ERR_CONNECTION_REFUSED"

**Browser Console (F12):**
```
GET http://localhost:8000/api/... 
Failed to connect
```

**Solutions:**
```bash
# 1. Check backend is running
curl http://localhost:8000/health

# 2. Verify proxy config in vite.config.js
# Should show:
# '/api': {
#   target: 'http://localhost:8000',
#   ...
# }

# 3. Restart frontend dev server
npm run dev

# 4. Check CORS is enabled on backend
# In app/main.py, check CORSMiddleware:
# allow_origins=["http://localhost:5173", "http://localhost:3000"]
```

#### "Token expired" or "401 Unauthorized"

**Problem:** Logged in but API returns 401

**Solutions:**
```javascript
// 1. Check token in localStorage
console.log(localStorage.getItem('token'));
// Should show long string starting with "eyJ"

// 2. Check token expiration
// Decode manually at: https://jwt.io
// Check "exp" field in payload

// 3. Clear storage and login again
localStorage.clear();
// Refresh page and login

// 4. Check API interceptor in services/api.js
// Should add: Authorization: Bearer {token}
```

---

### Docker Issues

#### "docker: command not found"

**Problem:** Docker is not installed or not in PATH

**Solutions:**
```bash
# 1. Install Docker Desktop
# https://www.docker.com/get-started

# 2. Verify installation
docker --version
docker-compose --version

# 3. Restart terminal after installation
# Close and reopen terminal

# 4. Add Docker to PATH (Windows)
# Docker installer should add automatically
# If not, add: C:\Program Files\Docker\Docker\resources\bin
```

#### "Cannot connect to Docker daemon"

**Problem:** "error during connect: ... connection refused"

**Solutions:**
```bash
# 1. Start Docker Desktop
# Windows/macOS: Click Docker.app
# Linux: sudo systemctl start docker

# 2. Check Docker is running
docker ps

# 3. Fix permissions (Linux)
sudo usermod -aG docker $USER
newgrp docker

# 4. Check Docker socket
docker run hello-world
```

#### "Port already in use"

**Problem:** "Address already in use" when starting containers

**Solutions:**
```bash
# Find process using port
# Windows:
netstat -ano | findstr :8000
# macOS/Linux:
lsof -i :8000

# Kill process
# Windows:
taskkill /PID 1234 /F
# macOS/Linux:
kill -9 1234

# Or use different port in docker-compose.yml:
services:
  backend:
    ports:
      - "8001:8000"  # Use 8001 instead of 8000
```

#### "MongoDB connection timeout in container"

**Problem:** Backend container can't connect to MongoDB

**Solutions:**
```bash
# 1. Check MongoDB container is healthy
docker-compose ps
# Should show "healthy" status

# 2. Check Docker network
docker network inspect ai_interviewer_network

# 3. Verify connection string
docker-compose exec backend env | grep MONGODB_URL
# Should show: mongodb://admin:password123@mongodb:27017/ai_interviewer

# 4. Restart services
docker-compose down
docker-compose up -d --force-recreate
```

---

### Database Issues

#### "E11000 duplicate key error"

**Problem:** Trying to insert duplicate email or unique field

**Solutions:**
```bash
# 1. Check for duplicate users
mongosh
use ai_interviewer
db.users.find({email: "test@example.com"})

# 2. Delete duplicate if testing
db.users.deleteOne({_id: ObjectId("...")})

# 3. Reset database for testing
db.dropDatabase()

# 4. Ensure unique indexes exist
db.users.createIndex({email: 1}, {unique: true})
```

#### "Document not found" error

**Problem:** API returns 404 when document should exist

**Solutions:**
```bash
# 1. Check document in MongoDB
mongosh
use ai_interviewer
db.interviews.findOne({_id: ObjectId("...")})

# 2. Verify ObjectId format
# Should be 24 character hex string: 507f1f77bcf86cd799439011

# 3. Check user_id matches
db.interviews.find({user_id: ObjectId("...")})

# 4. Check status/state of document
# May be marked as deleted or archived
```

---

## Frequently Asked Questions

### General Questions

**Q: Is this free to use?**

A: Yes! The MVP is completely free. We're planning premium tiers in the future but current version has no restrictions.

**Q: Can I use my own resume file?**

A: Yes! Upload any PDF or DOCX resume. It will be parsed and analyzed.

**Q: What job domains are supported?**

A: Currently: Backend, Frontend, Fullstack, DevOps, Data, Mobile. More coming soon!

**Q: Can I retake interviews?**

A: Yes, you can create unlimited interviews. Each one generates new questions based on domain and your resume.

---

### Technical Questions

**Q: What happens to my data?**

A: All data is stored in MongoDB on the backend. You own your data and can delete it anytime. We don't share data with third parties.

**Q: Is my password secure?**

A: Yes! Passwords are hashed with bcrypt using salt=12. Never stored in plain text.

**Q: Can I export my interview results?**

A: Currently, you can see results in the dashboard. Export feature coming in Phase 4. You can screenshot results.

**Q: How long are tokens valid?**

A: Access tokens expire after 30 minutes. You'll be automatically logged out. Login again to continue.

---

### Resume Analysis Questions

**Q: How accurate is the ATS score?**

A: Our ATS score is based on Gemini AI analysis of resume format, keyword density, and structure. It's ~85% accurate but check real ATS tools for final verification.

**Q: Will following suggestions guarantee a job?**

A: Following suggestions will improve your chances by helping you pass ATS filters and answer questions better. But interviews have many factors beyond resume matching.

**Q: Can I see what the AI thinks about my resume?**

A: Yes! The Resume Match Analysis section shows exactly what skills are missing, what's matched, and specific improvement suggestions.

**Q: How does the skill matching work?**

A: We extract skills from both your resume and job description using Gemini AI, then compare them. It also looks for keywords like "Python", "React", etc.

---

### Interview Questions

**Q: Are questions always different?**

A: Yes! Questions are generated uniquely each time based on:
- Your resume content
- The job description
- The domain selected
- The role specified

**Q: Can I practice the same interview twice?**

A: You can create multiple interviews for the same job, but questions will be different each time.

**Q: What if I don't know the answer to a question?**

A: You can skip the question (moves to next). Skipped questions get low scores but won't block you from other questions.

**Q: Is there a time limit?**

A: Yes, 2 minutes per question. When time runs out, answer is auto-submitted. You can submit early.

**Q: Can I go back to previous questions?**

A: No, it's designed to be forward-only like real interviews. This encourages thinking through answers completely.

---

### Scoring Questions

**Q: How is my score calculated?**

A: 
- Each answer scored 0-100 by Gemini AI
- Criteria: technical accuracy (40%), relevance (30%), communication (20%), completeness (10%)
- Overall score = average of all question scores

**Q: What's a good score?**

A: 
- 80+: Excellent, very competitive
- 70-79: Good, ready to interview
- 60-69: Fair, needs improvement
- Below 60: Needs significant practice

**Q: Why did I get a low score?**

A: Check the feedback on results page. Common reasons:
- Answer didn't address the question fully
- Missing technical details
- Poor explanation/communication
- Incomplete thoughts

**Q: Can I retake an interview for a better score?**

A: Yes! Create a new interview. Results are saved separately so you can track your progress.

---

### Technical Troubleshooting Questions

**Q: Why is the API slow?**

A: Possible causes:
- Gemini API is slow (takes 2-5 seconds)
- MongoDB query is slow (missing indexes)
- Network latency
- Try checking backend logs: `docker-compose logs backend`

**Q: Why did my file upload fail?**

A: Check:
- File is PDF or DOCX (not DOC, not other formats)
- File is less than 10MB
- No special characters in filename
- Sufficient disk space

**Q: Can I see backend errors in frontend?**

A: Check browser console (F12) for error messages. But some sensitive errors are hidden for security. Check backend logs for details.

**Q: How do I view backend logs?**

A: 
```bash
# Docker:
docker-compose logs backend -f

# Local:
Logs show in terminal where you started uvicorn
```

---

### Deployment Questions

**Q: Can I deploy this myself?**

A: Yes! See DOCKER.md for containerization and deployment guides.

**Q: What Cloud providers are supported?**

A: Any cloud that supports:
- Docker containers (AWS ECS, Google Cloud Run, Azure Container Instances)
- Kubernetes (GKE, EKS, AKS)
- Traditional servers (VPS hosting)

**Q: What's the minimum infrastructure needed?**

A: For production:
- 2GB RAM minimum (backend container)
- 1GB RAM for MongoDB
- 1 vCPU minimum
- 10GB storage (resumes, logs)

---

### Account & Security Questions

**Q: Can I delete my account?**

A: Feature is coming soon. For now, contact support@aiinterviewer.com

**Q: Is my email verified?**

A: Currently no email verification. Coming in next release.

**Q: Can multiple people use same account?**

A: Yes technically, but not recommended. Each person should have their own account for accurate analytics.

**Q: What if I forget my password?**

A: Password reset feature coming soon. For now, use MongoDB to reset (dangerous!) or contact support.

**Q: Is 2FA supported?**

A: Not yet. Coming in security enhancements phase.

---

## Debug Mode

Enable debug logging for troubleshooting:

**Backend Debug Mode:**

```bash
# Set in .env
DEBUG=True

# Check logs
docker-compose logs backend -f

# Or locally:
# Logs appear in terminal running uvicorn
```

**Frontend Debug Mode:**

```javascript
// In frontend/src/services/api.js, add:
api.interceptors.response.use(
  response => {
    console.log('[API Response]', response.config.url, response.status);
    return response;
  },
  error => {
    console.error('[API Error]', error.config.url, error.status, error.message);
    return Promise.reject(error);
  }
);
```

**MongoDB Debug:**

```bash
# Enable MongoDB verbose logging
# In docker-compose.yml:
services:
  mongodb:
    command: mongod --logLevel debug

# Or via connection:
mongosh --eval "db.adminCommand({getParameter:1, logLevel:1})"
```

---

## Performance Optimization Tips

### Frontend Performance

```bash
# 1. Check bundle size
npm run build
# Check dist/ size

# 2. Analyze performance
# Chrome DevTools → Lighthouse
# Run audit and check scores

# 3. Monitor Network tab
# F12 → Network
# Check each request takes <200ms
```

### Backend Performance

```bash
# 1. Monitor API response times
docker-compose logs backend | grep "Uvicorn running"

# 2. Add caching
# See: app/core/config.py

# 3. Check MongoDB indexes
mongosh
use ai_interviewer
db.interviews.getIndexes()

# 4. Profile queries
# Enable profiling: db.setProfilingLevel(2)
```

### Database Performance

```bash
# 1. Create indexes
db.users.createIndex({email: 1})
db.resumes.createIndex({user_id: 1})
db.interviews.createIndex({user_id: 1, created_at: -1})

# 2. Check query plans
db.interviews.find({user_id: ObjectId(...)}).explain("executionStats")

# 3. Monitor connections
db.serverStatus()
```

---

## Getting Help

**When reporting issues, include:**

1. **Environment:**
   - Docker or Local?
   - OS (Windows/macOS/Linux)?
   - Python/Node version?

2. **Steps to reproduce:**
   - Exact steps that cause issue
   - Error message text

3. **Logs:**
   - Backend logs: `docker-compose logs backend`
   - Frontend logs: Browser console (F12)
   - MongoDB logs: `docker-compose logs mongodb`

4. **Screenshots:**
   - Screenshot of error
   - Browser DevTools console output

**Support Channels:**
- GitHub Issues: Create detailed issue
- Email: support@aiinterviewer.com
- Discord: [Join community](https://discord.gg/aiinterviewer)

---

## Quick Reset

If stuck, try the nuclear option:

```bash
# Docker
docker-compose down -v
docker-compose up -d
# Wait 1-2 minutes for services to start

# Local
# Stop both servers (Ctrl+C)
# Delete: backend/uploads/*
# Delete: frontend/node_modules
cd backend && rm -rf venv
pip install -r requirements.txt
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

---

## Still Having Issues?

1. Check this document for your specific error
2. Check GitHub Issues for similar problems
3. Check backend/frontend logs for clues
4. Try the "Quick Reset" section above
5. Create GitHub issue with all details from "Getting Help"
6. Email support@aiinterviewer.com

We're here to help! 🚀

Happy troubleshooting!
