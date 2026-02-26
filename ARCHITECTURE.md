# Project Architecture & Design

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────┬───────────────┬────────────┬──────────────────┐   │
│  │  Login   │  Dashboard    │  Setup     │  Interview       │   │
│  │          │               │  (Resume  │  Session         │   │
│  │          │               │   + JD)   │  + Timer         │   │
│  └──────────┴───────────────┴────────────┴──────────────────┘   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Results (Resume Match Analysis - KEY DIFFERENTIATOR)      │ │
│  │  - ATS Score      - Matched Skills   - Improvement Tips   │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (HTTP + JWT)
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Authentication Endpoints (JWT)                          │  │
│  │  - Register, Login, Refresh, Profile                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Resource Endpoints                                      │  │
│  │  - Resume (Upload, List, Get, Delete)                   │  │
│  │  - Interview (Create, Submit Answer, Complete)          │  │
│  │  - Analytics (Dashboard, Domain Stats, Suggestions)     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Business Logic Services                                 │  │
│  │  ┌────────────────────┐  ┌──────────────────────────┐   │  │
│  │  │ Resume Parser      │  │ JD Resume Analyzer ⭐    │   │  │
│  │  │ (PDF/DOCX text)    │  │ (Gemini AI Compare)      │   │  │
│  │  └────────────────────┘  └──────────────────────────┘   │  │
│  │  ┌────────────────────┐  ┌──────────────────────────┐   │  │
│  │  │ Question           │  │ Interview Evaluator      │   │  │
│  │  │ Generator          │  │ (Score Answers)          │   │  │
│  │  │ (Personalized)     │  │                          │   │  │
│  │  └────────────────────┘  └──────────────────────────┘   │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │ Analytics Engine (Performance Metrics)           │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Gemini AI API                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ - Compare Resume vs JD → ATS Score + Skill Gaps         │  │
│  │ - Generate Questions based on Role + Domain + Resume    │  │
│  │ - Evaluate Answers → Score + Feedback                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      MongoDB Database                           │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐   │
│  │   Users     │  │  Resumes    │  │   Interviews         │   │
│  └─────────────┘  └─────────────┘  └──────────────────────┘   │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Analytics Cache (Performance Metrics, Trends)        │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Clean Architecture Design

### Backend Layers

```
┌─────────────────────────────────────────────────┐
│            API Layer (FastAPI)                   │
│  Endpoints: /api/auth, /api/resume, /api/...    │
│  - Request validation                            │
│  - Response formatting                           │
│  - HTTP status codes                             │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│          Business Logic Services                 │
│  ┌──────────────────────────────────────────┐   │
│  │ ResumeParse: Extract text from PDF/DOCX  │   │
│  │ JDAnalyzer: Compare resume vs job desc   │   │
│  │ QuestionGenerator: Create interview Q's  │   │
│  │ InterviewEvaluator: Score answers        │   │
│  │ Analytics: Compute metrics               │   │
│  └──────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│         Data Access & External APIs              │
│  ┌──────────────────────────────────────────┐   │
│  │ Database: MongoDB operations              │   │
│  │ External: Gemini AI API calls             │   │
│  │ Files: PDF/DOCX parsing libraries         │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### Frontend Architecture

```
┌──────────────────────────────────────────────────┐
│               Pages (Routes)                      │
│  ┌───────┬──────────┬────────────┬──────────┐   │
│  │ Login │ Dashboard │ Setup      │ Interview│   │
│  │ Reg.  │ (Stats)   │ (3-step)   │ Session │   │
│  └───────┴──────────┴────────────┴──────────┘   │
│  ┌────────────────────────────────────────────┐  │
│  │  Results (Resume Match Analysis)           │  │
│  └────────────────────────────────────────────┘  │
└────────────────┬─────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────┐
│        Component & State Layer                    │
│  ┌─────────────┐      ┌──────────────────────┐  │
│  │ Components: │      │ State Management:    │  │
│  │ - UI.jsx    │      │ - AuthContext        │  │
│  │ - Navbar    │      │ - InterviewContext   │  │
│  └─────────────┘      └──────────────────────┘  │
└────────────────┬─────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────┐
│          Service Layer                            │
│  - API Client (axios with interceptors)          │
│  - Authentication handling                        │
│  - Token management                               │
└────────────────┬─────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────┐
│          Styling & Utilities                      │
│  - CSS Modules (component scoped)                 │
│  - Global CSS (design system)                     │
│  - Helper functions                               │
└──────────────────────────────────────────────────┘
```

## Data Flow

### Interview Creation Flow

```
1. User uploads resume (PDF/DOCX)
   ↓
2. Backend: Resume Parser extracts text
   ↓
3. User enters job details (role, domain, JD, question count)
   ↓
4. Backend: Question Generator (Gemini AI) creates personalized questions
   Based on: Job role, Domain, Resume text, Job description
   ↓
5. Frontend: Display questions, user starts interview
```

### Interview Completion Flow

```
1. User answers all questions
   Each answer → Backend: InterviewEvaluator (Gemini AI)
   → Returns: Score (0-100) + Feedback
   ↓
2. User completes interview
   ↓
3. Backend: JDResumeAnalyzer (Gemini AI) compares resume vs JD
   Returns: {
     ats_score,
     matched_skills,
     missing_skills,
     keyword_gaps,
     experience_gap,
     improvement_suggestions,
     ats_optimization_tips
   }
   ↓
4. Frontend: Results page displays
   - Overall score
   - Resume Match Analysis (KEY DIFFERENTIATOR)
   - Question performance breakdown
   - Suggestions for improvement
```

## Key Differentiator: Resume vs JD Analysis

### The Analysis Process

```
Input:
├── Resume (parsed text from PDF/DOCX)
├── Job Description (user input)
└── Job Role (user input)

Process:
↓
Gemini AI Analysis:
├── Extract required skills from JD
├── Extract candidate skills from resume
├── Calculate skill match percentage
├── Generate content suggestions
└── Create ATS optimization tips

Output:
├── ats_score (0-100): How well resume passes ATS
├── matched_skills: Skills found in both
├── missing_skills: Important skills not in resume
├── keyword_gaps: Keywords/techs to add
├── experience_gap: Alignment with experience level
├── improvement_suggestions: How to strengthen resume
└── ats_optimization_tips: ATS keyword insertion tips
```

### Why This Matters

Modern hiring uses **Applicant Tracking Systems (ATS)** that automatically filter resumes:
- Only relevant keywords pass through
- Generic resumes get rejected
- Missing critical skills = rejection

**Our Platform Solution**:
- Tells candidates exactly what's missing
- Shows which skills to highlight
- Provides ATS optimization tips
- Help candidates get past the first filter

## Database Schema

### Users Collection
```
{
  _id: ObjectId,
  name: String,
  email: String (unique, indexed),
  password_hash: String (bcrypt),
  created_at: DateTime,
  updated_at: DateTime
}
```

### Resumes Collection
```
{
  _id: ObjectId,
  user_id: ObjectId (indexed),
  file_name: String,
  file_type: String (pdf|docx),
  file_path: String,
  parsed_text: String (full resume text),
  uploaded_at: DateTime
}
```

### Interviews Collection
```
{
  _id: ObjectId,
  user_id: ObjectId (indexed),
  resume_id: ObjectId (indexed),
  job_role: String,
  domain: String,
  job_description: String,
  questions: [String],
  answers: [
    {
      question_index: Number,
      answer: String,
      score: Number (0-100),
      feedback: String,
      strengths: [String],
      improvements: [String]
    }
  ],
  overall_score: Number,
  jd_analysis: {
    ats_score: Number,
    matched_skills: [String],
    missing_skills: [String],
    keyword_gaps: [String],
    experience_gap: String,
    improvement_suggestions: [String],
    ats_optimization_tips: [String]
  },
  status: String (in_progress|completed),
  created_at: DateTime,
  updated_at: DateTime
}
```

### Analytics Cache Collection
```
{
  _id: ObjectId,
  user_id: ObjectId (indexed),
  interview_id: ObjectId,
  domain: String,
  score: Number,
  date: DateTime,
  cached_metrics: {
    average_score: Number,
    best_score: Number,
    interview_count: Number,
    domains_count: Numbers,
    trend: String
  }
}
```

## API Architecture

### Request Flow with JWT

```
1. Client sends request
   ↓
2. API Middleware: CORS check
   ↓
3. Protected routes: JWT validation
   - Extract token from Authorization header
   - Decode JWT
   - Verify signature
   - Check expiration
   ↓
4. Dependency Injection: get_current_user()
   - Returns user_id if valid
   ↓
5. Endpoint handler processes request
   ↓
6. Response returned with status code
```

## Security Architecture

### Password Security
```
User Input Password
        ↓
bcrypt.hashpw(password, salt=12)
        ↓
Hash stored in database (never plain text)
        ↓
Login: bcrypt.checkpw(input, hash)
        ↓
Match → Success / No match → Failure
```

### Token Security
```
User registers/logins
        ↓
JWT created with:
- user_id (payload)
- exp (expiration time)
- secret key (signature)
        ↓
Token sent to client
        ↓
Client stores in localStorage
        ↓
Each request:
- Token in Authorization: Bearer header
- Backend verifies signature with secret key
- Check expiration
        ↓
Valid → Request proceeds / Invalid → 401 Unauthorized
```

## Deployment Architecture

### Development
```
┌─────────┐           ┌─────────┐
│Frontend │           │ Backend │
│  :5173  │◄─────────►│  :8000  │
└─────────┘           └─────────┘
                            ↓
                       ┌──────────┐
                       │ MongoDB  │
                       │ :27017   │
                       └──────────┘
```

### Docker Container Deployment
```
┌─────────────────────────────────────┐
│         Docker Network              │
│  ┌──────────┐  ┌──────────┐        │
│  │Frontend  │  │ Backend  │        │
│  │:3000     │  │ :8000    │        │
│  └──────────┘  └──────────┘        │
│       ↓              ↓               │
│  ┌──────────────────────────┐       │
│  │    MongoDB Container     │       │
│  │      :27017              │       │
│  └──────────────────────────┘       │
└─────────────────────────────────────┘
        ↓
   Exposed Ports
   - Frontend: localhost:3000
   - Backend: localhost:8000
```

## Performance Considerations

### Frontend Optimization
- Code splitting per route (lazy loading)
- CSS modules prevent style conflicts
- Context API prevents unnecessary re-renders
- Async image loading
- Optimized bundle size (~50KB gzipped)

### Backend Optimization
- Async FastAPI handlers (non-blocking)
- Connection pooling for MongoDB
- JWT caching to avoid repeated DB queries
- File streaming for large uploads
- Gemini API response caching for similar queries

### Database Optimization
- Indexed queries on user_id, interview_id, resume_id
- Pagination for list endpoints
- Analytics cache for aggregations
- TTL indexes for cleanup

## Scalability Considerations

### Current Setup (Single Server)
- Works for ~100 concurrent users
- MongoDB on same server
- Suitable for MVP/testing

### Production Scaling
```
Level 1: Kubernetes Orchestration
├── Frontend replicas (load balanced)
├── Backend replicas (auto-scaled)
└── MongoDB Atlas (managed)

Level 2: Microservices Split
├── Auth Service
├── Resume Service
├── Interview Service
├── Analytics Service
└── Shared Database

Level 3: Advanced
├── API Gateway (Kong, AWS API Gateway)
├── Message Queue (Redis, RabbitMQ)
├── Cache Layer (Redis)
├── CDN for static assets
└── Multi-region deployment
```

## Technology Choices Rationale

| Component | Choice | Why |
|-----------|--------|-----|
| Backend Framework | FastAPI | Async, fast, auto-docs, Pydantic validation |
| Frontend Framework | React+Vite | Fast dev server, minimal config, modern tooling |
| Database | MongoDB | Document model fits interview data, flexible schema |
| AI/LLM | Gemini API | Superior quality, reasonable pricing, easy integration |
| Auth | JWT | Stateless, scalable, industry standard |
| Styling | CSS Modules | Scoped styles, no conflicts, lightweight |
| Deployment | Docker | Consistent environment, easy scaling, cloud-ready |

---

## Conclusion

This architecture provides:
- ✅ Clean separation of concerns
- ✅ Scalable from MVP to enterprise
- ✅ Security-first design
- ✅ Production-ready infrastructure
- ✅ Clear, maintainable code structure

The key differentiator (Resume vs JD Analysis) is deeply integrated throughout the system, providing real value to users preparing for interviews.
