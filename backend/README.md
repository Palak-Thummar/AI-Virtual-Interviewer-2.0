# Backend Setup Guide

## Prerequisites

- Python 3.8 or higher
- MongoDB (local or remote)
- Gemini API key from Google Cloud

## Installation Steps

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings:
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
- `MONGODB_URL`: MongoDB connection string
- `MONGODB_DB`: Database name
- `GEMINI_API_KEY`: Google Gemini API key
- `SECRET_KEY`: JWT secret (change in production!)

### 4. Create MongoDB Database

```bash
# If using MongoDB locally, ensure it's running:
# mongod

# Create database (MongoDB creates it automatically on first write)
```

### 5. Run Development Server

```bash
# From backend directory:
uvicorn app.main:app --reload

# Server will run on: http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/      # API route handlers
│   │   ├── dependencies.py # JWT dependency injection
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py       # Settings management
│   │   ├── database.py     # MongoDB connection
│   │   ├── security.py     # Password & JWT utils
│   │   └── __init__.py
│   ├── models/
│   │   ├── database.py     # Pydantic models for DB
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── api.py          # Request/response schemas
│   │   └── __init__.py
│   ├── services/
│   │   ├── resume_parser.py        # Extract resume text
│   │   ├── jd_resume_analyzer.py   # Compare resume vs JD
│   │   ├── question_generator.py   # Generate questions
│   │   ├── interview_evaluator.py  # Score answers
│   │   ├── analytics.py            # Calculate metrics
│   │   └── __init__.py
│   ├── utils/
│   │   ├── helpers.py      # Helper functions
│   │   └── __init__.py
│   ├── main.py             # FastAPI app factory
│   └── __init__.py
├── uploads/                # Resume uploads directory
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Using the API

### Health Check
```bash
curl http://localhost:8000/health
```

### Register User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

### Upload Resume
```bash
curl -X POST http://localhost:8000/api/resume/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@resume.pdf"
```

## API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## Key Services

### Resume Parser (`resume_parser.py`)
- Extracts text from PDF and DOCX files
- Supports multiple pages
- Handles tables in Word documents

### JD Resume Analyzer (`jd_resume_analyzer.py`)
- Compares resume against job description
- Calculates ATS score
- Identifies skill gaps
- Generates improvement suggestions

### Question Generator (`question_generator.py`)
- Creates personalized interview questions
- Based on role, domain, resume, and JD
- Generates follow-up questions
- Fallback questions if AI fails

### Interview Evaluator (`interview_evaluator.py`)
- Scores candidate answers
- Provides constructive feedback
- Calculates session metrics
- Generates interview recommendations

### Analytics (`analytics.py`)
- Calculates average scores
- Tracks domain performance
- Generates improvement trends
- Provides user insights

## Error Handling

The API returns standardized error responses:

```json
{
  "detail": "Error message here"
}
```

Common HTTP status codes:
- `200`: OK
- `201`: Created
- `400`: Bad Request (validation error)
- `401`: Unauthorized (auth error)
- `404`: Not Found
- `409`: Conflict (e.g., email already registered)
- `500`: Internal Server Error

## Development Tips

### Hot Reload
The `--reload` flag enables hot reload. Changes to Python files will automatically restart the server.

### Debug Mode
Set `DEBUG=True` in `.env` to enable debug mode:
```bash
DEBUG=True
```

### Database Reset
To reset MongoDB:
```bash
# Using MongoDB shell
mongo ai_interviewer
db.dropDatabase()
```

### Logging
Check logs in the terminal where uvicorn is running for debugging.

## Testing

### Manual Testing with cURL

```bash
# Test auth endpoint
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","password":"pass123"}'

# Get token from response, use it:
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/auth/me
```

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Register
response = requests.post(f"{BASE_URL}/api/auth/register", json={
    "name": "John Doe",
    "email": "john@test.com",
    "password": "testpass123"
})
token = response.json()["access_token"]

# Use token in headers
headers = {"Authorization": f"Bearer {token}"}

# Get user profile
response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
print(response.json())
```

## Production Deployment

### 1. Update Environment
```bash
# Production .env
DEBUG=False
SECRET_KEY=your-very-secure-random-key
MONGODB_URL=mongodb://prod-server:27017
# ... other prod settings
```

### 2. Use Production Server
```bash
# Using Gunicorn + Uvicorn
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

Build and run:
```bash
docker build -t ai-interviewer-backend .
docker run -p 8000:8000 --env-file .env ai-interviewer-backend
```

## Troubleshooting

### MongoDB Connection Error
```
Error: Failed to connect to MongoDB
```
- Ensure MongoDB is running
- Check MONGODB_URL in .env
- Verify network connectivity

### Gemini API Error
```
Error: Gemini API error
```
- Verify GEMINI_API_KEY is correct
- Check API quota and billing
- Ensure API is enabled in Google Cloud

### File Upload Error
```
Error: Failed to save resume
```
- Check write permissions in uploads/ directory
- Verify file size is under 10MB
- Ensure file is PDF or DOCX

## Support

For issues or questions:
1. Check API logs in terminal
2. Visit Swagger UI at `/docs` for endpoint documentation
3. Review error messages in response body
4. Create an issue in the repository

## Next Steps

1. Start the frontend development server
2. Create a user account
3. Upload a resume
4. Start an interview!

---

Happy coding! 🚀
