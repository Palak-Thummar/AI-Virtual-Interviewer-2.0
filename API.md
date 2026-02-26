# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication

All protected endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

## Response Format

All responses use JSON format:

```json
{
  "data": {
    // Response data
  },
  "status": 200,
  "message": "Success"
}
```

Errors return:
```json
{
  "detail": "Error message here"
}
```

---

## Authentication Endpoints

### Register New User
**POST** `/api/auth/register`

Create a new user account.

**Request:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "_id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid email format or email already registered
- `422 Unprocessable Entity`: Missing required fields

---

### Login User
**POST** `/api/auth/login`

Login with email and password.

**Request:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "_id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `404 Not Found`: User not found

---

### Get Current User Profile
**GET** `/api/auth/me`

Retrieve current authenticated user's profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid token

---

### Refresh Access Token
**POST** `/api/auth/refresh`

Get a new access token.

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## Resume Endpoints

### Upload Resume
**POST** `/api/resume/upload`

Upload and parse a resume file (PDF or DOCX).

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request:**
- Form data with file field

**Response (201 Created):**
```json
{
  "_id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "file_name": "resume_john_doe.pdf",
  "file_type": "pdf",
  "parsed_text": "John Doe\nSoftware Engineer...",
  "uploaded_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid file type or size exceeds limit
- `401 Unauthorized`: Missing authentication
- `413 Payload Too Large`: File larger than 10MB

---

### List User's Resumes
**GET** `/api/resume/my/list`

Get list of all resumes uploaded by current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of resumes to skip (default: 0)
- `limit` (optional): Maximum resumes to return (default: 10)

**Response (200 OK):**
```json
[
  {
    "_id": "507f1f77bcf86cd799439012",
    "file_name": "resume_john_doe.pdf",
    "file_type": "pdf",
    "uploaded_at": "2024-01-15T10:30:00Z"
  },
  {
    "_id": "507f1f77bcf86cd799439013",
    "file_name": "resume_updated.docx",
    "file_type": "docx",
    "uploaded_at": "2024-01-14T15:20:00Z"
  }
]
```

---

### Get Resume Details
**GET** `/api/resume/{resume_id}`

Get detailed information about a specific resume.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "file_name": "resume_john_doe.pdf",
  "file_type": "pdf",
  "parsed_text": "John Doe\nSoftware Engineer...",
  "uploaded_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Resume not found
- `403 Forbidden`: Resume belongs to another user

---

### Delete Resume
**DELETE** `/api/resume/{resume_id}`

Delete a resume file.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Resume deleted successfully"
}
```

**Error Responses:**
- `404 Not Found`: Resume not found
- `403 Forbidden`: Resume belongs to another user

---

## Interview Endpoints

### Create Interview
**POST** `/api/interview/create`

Create a new interview session with AI-generated questions.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "job_role": "Senior Backend Engineer",
  "domain": "Backend",
  "job_description": "We're looking for a senior backend engineer...",
  "resume_id": "507f1f77bcf86cd799439012",
  "num_questions": 5
}
```

**Response (201 Created):**
```json
{
  "_id": "507f1f77bcf86cd799439014",
  "user_id": "507f1f77bcf86cd799439011",
  "job_role": "Senior Backend Engineer",
  "domain": "Backend",
  "job_description": "We're looking for a senior backend engineer...",
  "resume_id": "507f1f77bcf86cd799439012",
  "questions": [
    "Tell us about your experience with microservices architecture",
    "How do you handle database optimization?",
    "Describe your approach to API design",
    "What's your experience with cloud platforms?",
    "How do you handle system scalability challenges?"
  ],
  "status": "in_progress",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input or resume not found
- `401 Unauthorized`: Missing authentication

---

### Get Interview Details
**GET** `/api/interview/{interview_id}`

Get interview session details.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439014",
  "user_id": "507f1f77bcf86cd799439011",
  "job_role": "Senior Backend Engineer",
  "domain": "Backend",
  "questions": ["Question 1", "Question 2", ...],
  "answers": [
    {
      "question_index": 0,
      "answer": "User's answer to question 1",
      "score": 78,
      "feedback": "Good understanding..."
    }
  ],
  "overall_score": 75,
  "status": "in_progress",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Submit Answer
**POST** `/api/interview/{interview_id}/submit-answer`

Submit answer to current question and get evaluation.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "question_index": 0,
  "answer": "I have 8 years of experience with microservices...",
  "duration_seconds": 85
}
```

**Response (200 OK):**
```json
{
  "question_index": 0,
  "score": 82,
  "feedback": "Excellent answer showing deep understanding...",
  "strengths": ["Clear explanation", "Relevant examples"],
  "improvements": ["Could mention testing strategies"],
  "next_question": "How do you handle database optimization?",
  "interview_progress": "1/5"
}
```

**Error Responses:**
- `404 Not Found`: Interview not found
- `400 Bad Request`: Invalid question index

---

### Complete Interview
**POST** `/api/interview/{interview_id}/complete`

Complete interview session and get final results with resume analysis.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "resume_id": "507f1f77bcf86cd799439012"
}
```

**Response (200 OK):**
```json
{
  "interview_id": "507f1f77bcf86cd799439014",
  "overall_score": 78,
  "status": "completed",
  "completed_at": "2024-01-15T11:15:00Z",
  "question_results": [
    {
      "question_index": 0,
      "question": "Tell us about your experience...",
      "answer": "I have 8 years...",
      "score": 82,
      "feedback": "Excellent answer..."
    }
  ],
  "resume_analysis": {
    "ats_score": 87,
    "matched_skills": ["Python", "FastAPI", "MongoDB", "Docker"],
    "missing_skills": ["Kubernetes", "GraphQL", "AWS"],
    "keyword_gaps": ["Cloud native", "CI/CD", "Agile"],
    "experience_gap": "Your experience aligns well with the role requirements. Consider adding cloud platform experience.",
    "improvement_suggestions": [
      "Add Kubernetes experience",
      "Include cloud/AWS projects",
      "Highlight CI/CD pipeline implementations"
    ],
    "ats_optimization_tips": [
      "Use action verbs like 'architected', 'optimized', 'engineered'",
      "Include specific metrics and achievements",
      "Add relevant keywords in skills section"
    ]
  },
  "recommendation": "Strong candidate! Ready to interview."
}
```

---

## Analytics Endpoints

### Get Dashboard Analytics
**GET** `/api/analytics/dashboard`

Get user's dashboard analytics summary.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "average_score": 76.5,
  "best_score": 88,
  "interview_count": 5,
  "domain_performance": [
    {
      "domain": "Backend",
      "average_score": 79,
      "interview_count": 3
    },
    {
      "domain": "DevOps",
      "average_score": 72,
      "interview_count": 2
    }
  ],
  "recent_interviews": [
    {
      "_id": "507f1f77bcf86cd799439014",
      "job_role": "Senior Backend Engineer",
      "domain": "Backend",
      "score": 78,
      "date": "2024-01-15T10:30:00Z"
    }
  ],
  "improvement_trend": {
    "last_5_interviews": [65, 68, 72, 75, 78],
    "trend": "improving"
  }
}
```

---

### Get Domain-Specific Performance
**GET** `/api/analytics/domain/{domain}`

Get performance statistics for a specific domain.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `domain`: Domain name (Backend, Frontend, DevOps, Data, Mobile, Fullstack)

**Response (200 OK):**
```json
{
  "domain": "Backend",
  "average_score": 79,
  "best_score": 88,
  "worst_score": 65,
  "interview_count": 3,
  "common_weak_areas": [
    "System design",
    "Database optimization"
  ],
  "most_improved_areas": [
    "API design",
    "Error handling"
  ]
}
```

---

### Get Improvement Suggestions
**GET** `/api/analytics/suggestions`

Get personalized improvement suggestions based on interview history.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "overall_suggestions": [
    "Work on system design questions",
    "Improve communication of technical concepts",
    "Practice database optimization problems"
  ],
  "domain_suggestions": {
    "Backend": [
      "Learn more about microservices patterns",
      "Practice API security implementation"
    ],
    "DevOps": [
      "Deep dive into Kubernetes orchestration",
      "Study CI/CD best practices"
    ]
  },
  "next_steps": [
    "Review weak areas from last interview",
    "Practice 3 more backend interviews",
    "Study the suggested topics"
  ]
}
```

---

### Get Interview History
**GET** `/api/analytics/interviews`

Get paginated list of user's past interviews.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of interviews to skip (default: 0)
- `limit` (optional): Maximum interviews to return (default: 10)
- `domain` (optional): Filter by domain

**Response (200 OK):**
```json
[
  {
    "_id": "507f1f77bcf86cd799439014",
    "job_role": "Senior Backend Engineer",
    "domain": "Backend",
    "score": 78,
    "status": "completed",
    "date": "2024-01-15T10:30:00Z",
    "question_count": 5,
    "duration_minutes": 15
  }
]
```

---

## Health Check

### Check Server Status
**GET** `/health`

Check if the backend server is running.

**Response (200 OK):**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Error Codes Reference

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad Request | Check request format and required fields |
| 401 | Unauthorized | Provide valid authentication token |
| 403 | Forbidden | Access denied - check resource ownership |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource already exists (e.g., email already registered) |
| 413 | Payload Too Large | File size exceeds limit (max 10MB) |
| 422 | Unprocessable Entity | Request validation failed |
| 500 | Server Error | Unexpected server error - check logs |

---

## Rate Limiting

Currently no rate limiting is implemented. Production deployments should implement rate limiting.

---

## Testing with cURL

### Register
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@test.com",
    "password": "testpass123"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@test.com",
    "password": "testpass123"
  }'
```

### Get Profile (with token)
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/auth/me
```

### Upload Resume
```bash
curl -X POST http://localhost:8000/api/resume/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@resume.pdf"
```

---

## Interactive Documentation

Visit **http://localhost:8000/docs** for interactive Swagger UI with request/response examples and ability to test endpoints directly.

---

## Support

For API issues or questions:
1. Check this documentation
2. Visit the interactive Swagger UI at `/docs`
3. Review backend logs for detailed error messages
4. Create an issue on GitHub
