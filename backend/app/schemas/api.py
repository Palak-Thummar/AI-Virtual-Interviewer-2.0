"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============= AUTH SCHEMAS =============

class UserRegister(BaseModel):
    """User registration request."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response without sensitive data."""
    id: str = Field(alias="_id")
    name: str
    email: EmailStr
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============= RESUME SCHEMAS =============

class ResumeResponse(BaseModel):
    """Resume response."""
    id: str = Field(alias="_id")
    user_id: str
    file_name: str
    file_type: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class ResumeUploadResponse(BaseModel):
    """Response after resume upload."""
    message: str
    resume_id: str
    file_name: str


# ============= INTERVIEW SETUP SCHEMAS =============

class InterviewSetup(BaseModel):
    """Setup for interview creation."""
    job_role: str = Field(..., min_length=1, max_length=100)
    domain: str = Field(..., min_length=1, max_length=50)
    job_description: str = Field(..., min_length=10)
    resume_id: str
    num_questions: Optional[int] = Field(default=None, ge=1, le=20)


class InterviewCreateResponse(BaseModel):
    """Response after creating interview."""
    interview_id: str
    job_role: str
    domain: str
    num_questions: int
    questions: List[str]


# ============= INTERVIEW SESSION SCHEMAS =============

class AnswerSubmission(BaseModel):
    """Answer submission during interview."""
    question_id: int = Field(..., ge=0)
    answer: str = Field(..., min_length=1)


class AnswerEvaluationResponse(BaseModel):
    """Response after evaluating answer."""
    question_id: int
    score: float
    feedback: str
    strengths: List[str]
    improvements: List[str]


# ============= RESULTS AND ANALYTICS SCHEMAS =============

class SkillMatch(BaseModel):
    """Skill matching information."""
    matched_skills: List[str]
    missing_skills: List[str]
    ats_score: float
    keyword_gaps: List[str]
    experience_gap: str


class ResumeSuggestion(BaseModel):
    """Resume improvement suggestions."""
    improvement_suggestions: List[str]
    ats_optimization_tips: List[str]


class InterviewResults(BaseModel):
    """Complete interview results."""
    interview_id: str
    overall_score: float
    domain: str
    job_role: str
    question_scores: List[AnswerEvaluationResponse]
    skill_match: SkillMatch
    resume_suggestions: ResumeSuggestion
    completed_at: datetime


class AnalyticsData(BaseModel):
    """Analytics data for dashboard."""
    average_score: float
    best_score: float
    interview_count: int
    domain_performance: dict  # domain -> avg score
    recent_interviews: List[dict]
    improvement_trend: List[dict]  # date -> score
