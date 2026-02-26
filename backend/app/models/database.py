"""
MongoDB database models using Pydantic for validation.
Defines the schema for all collections.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError(f"Invalid ObjectId: {v}")
        return ObjectId(v)

    def __repr__(self):
        return f"ObjectId('{self}')"


# ============= USER MODELS =============

class UserInDB(BaseModel):
    """User model stored in database."""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    name: str
    email: EmailStr
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ============= RESUME MODELS =============

class ResumeInDB(BaseModel):
    """Resume model for database storage."""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    user_id: PyObjectId
    file_path: str
    file_name: str
    parsed_text: str
    file_type: str  # "pdf" or "docx"
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ============= INTERVIEW MODELS =============

class QuestionAnswer(BaseModel):
    """Question and answer pair during interview."""
    question_id: int
    question: str
    answer: str
    score: float
    feedback: str
    strengths: List[str] = []
    improvements: List[str] = []


class InterviewInDB(BaseModel):
    """Interview session model."""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    user_id: PyObjectId
    job_role: str
    domain: str
    job_description: str
    resume_id: PyObjectId
    questions: List[str] = []
    answers: List[QuestionAnswer] = []
    overall_score: float = 0.0
    status: str = "pending"  # pending, in_progress, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ============= ANALYTICS MODELS =============

class AnalyticsInDB(BaseModel):
    """Analytics data for user performance."""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    user_id: PyObjectId
    interview_id: PyObjectId
    domain: str
    score: float
    date: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
