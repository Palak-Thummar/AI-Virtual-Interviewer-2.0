"""
Settings API endpoints.
Independent configuration module for profile, security, preferences, resume,
notifications, and privacy controls.
"""

from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, EmailStr, Field

from app.api.dependencies import get_current_user
from app.core.database import get_collection
from app.core.security import hash_password, verify_password
from app.services.resume_parser import clean_text, extract_resume_text

router = APIRouter(prefix="/api/settings", tags=["settings"])

ALLOWED_DIFFICULTY = {"easy", "medium", "hard"}
ALLOWED_QUESTION_TYPES = {"mcq", "coding", "theory"}
MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024

DEFAULT_PREFERENCES = {
    "default_question_count": 5,
    "difficulty": "medium",
    "question_types": ["mcq", "coding"],
    "include_dsa": True,
    "include_system_design": False,
}

DEFAULT_NOTIFICATIONS = {
    "email_notifications": True,
    "interview_reminders": True,
    "weekly_summary": True,
    "skill_suggestions": True,
}


def _error(message: str, code: str = "validation_error", http_status: int = status.HTTP_400_BAD_REQUEST):
    raise HTTPException(status_code=http_status, detail={"error": code, "message": message})


def _user_object_id(user_id: str) -> ObjectId:
    return user_id if isinstance(user_id, ObjectId) else ObjectId(user_id)


def _extract_skills(parsed_text: str) -> List[str]:
    if not parsed_text:
        return []

    known_skills = [
        "Java", "Spring", "Spring Boot", "Python", "FastAPI", "Django", "Flask", "Node.js", "React",
        "TypeScript", "JavaScript", "MongoDB", "MySQL", "PostgreSQL", "Redis", "Docker", "Kubernetes",
        "AWS", "GCP", "Azure", "REST", "GraphQL", "Microservices", "System Design", "DSA",
        "Kafka", "RabbitMQ", "Git", "CI/CD", "JUnit", "Pytest"
    ]

    lowered = parsed_text.lower()
    extracted = [skill for skill in known_skills if skill.lower() in lowered]
    unique = []
    seen = set()
    for item in extracted:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:30]


def _ensure_user_fields(user_doc: Dict) -> Dict:
    full_name = user_doc.get("full_name") or user_doc.get("name") or ""
    primary_role = user_doc.get("primary_role") or ""
    experience_level = user_doc.get("experience_level") or ""
    profile_image_url = user_doc.get("profile_image_url") or ""

    return {
        "id": str(user_doc.get("_id")),
        "full_name": full_name,
        "email": user_doc.get("email", ""),
        "primary_role": primary_role,
        "experience_level": experience_level,
        "profile_image_url": profile_image_url,
        "created_at": user_doc.get("created_at"),
    }


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=120)
    primary_role: str = Field(default="", max_length=120)
    experience_level: str = Field(default="", max_length=80)
    email: Optional[EmailStr] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)


class PreferencesRequest(BaseModel):
    default_question_count: int = Field(..., ge=1, le=20)
    difficulty: str
    question_types: List[str]
    include_dsa: bool
    include_system_design: bool


class NotificationsRequest(BaseModel):
    email_notifications: bool
    interview_reminders: bool
    weekly_summary: bool
    skill_suggestions: bool


@router.get("/profile")
async def get_profile(current_user_id: str = Depends(get_current_user)):
    users_collection = get_collection("users")
    user = users_collection.find_one({"_id": _user_object_id(current_user_id)})
    if not user:
        _error("User not found", code="not_found", http_status=status.HTTP_404_NOT_FOUND)

    return _ensure_user_fields(user)


@router.put("/profile")
async def update_profile(payload: ProfileUpdateRequest, current_user_id: str = Depends(get_current_user)):
    users_collection = get_collection("users")
    user_id = _user_object_id(current_user_id)
    existing = users_collection.find_one({"_id": user_id})
    if not existing:
        _error("User not found", code="not_found", http_status=status.HTTP_404_NOT_FOUND)

    if payload.email and payload.email != existing.get("email"):
        _error("Email change requires verification and is currently disabled")

    users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "full_name": payload.full_name.strip(),
                "name": payload.full_name.strip(),
                "primary_role": payload.primary_role.strip(),
                "experience_level": payload.experience_level.strip(),
                "updated_at": datetime.utcnow(),
            }
        }
    )

    updated = users_collection.find_one({"_id": user_id})
    return _ensure_user_fields(updated)


@router.put("/change-password")
async def change_password(payload: ChangePasswordRequest, current_user_id: str = Depends(get_current_user)):
    if payload.new_password != payload.confirm_password:
        _error("New password and confirmation password do not match")

    users_collection = get_collection("users")
    user = users_collection.find_one({"_id": _user_object_id(current_user_id)})
    if not user:
        _error("User not found", code="not_found", http_status=status.HTTP_404_NOT_FOUND)

    if not verify_password(payload.current_password, user.get("password_hash", "")):
        _error("Current password is incorrect", code="invalid_credentials", http_status=status.HTTP_401_UNAUTHORIZED)

    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": hash_password(payload.new_password), "updated_at": datetime.utcnow()}}
    )

    return {"message": "Password updated successfully"}


@router.get("/preferences")
async def get_preferences(current_user_id: str = Depends(get_current_user)):
    collection = get_collection("user_preferences")
    user_id = _user_object_id(current_user_id)

    existing = collection.find_one({"user_id": user_id})
    if not existing:
        now = datetime.utcnow()
        doc = {
            "user_id": user_id,
            **DEFAULT_PREFERENCES,
            "created_at": now,
            "updated_at": now,
        }
        collection.update_one({"user_id": user_id}, {"$set": doc}, upsert=True)
        existing = doc

    return {
        "default_question_count": int(existing.get("default_question_count", 5)),
        "difficulty": str(existing.get("difficulty", "medium")).lower(),
        "question_types": list(existing.get("question_types", ["mcq", "coding"])),
        "include_dsa": bool(existing.get("include_dsa", True)),
        "include_system_design": bool(existing.get("include_system_design", False)),
        "updated_at": existing.get("updated_at"),
    }


@router.put("/preferences")
async def update_preferences(payload: PreferencesRequest, current_user_id: str = Depends(get_current_user)):
    difficulty = payload.difficulty.lower().strip()
    if difficulty not in ALLOWED_DIFFICULTY:
        _error("difficulty must be one of: easy, medium, hard")

    normalized_types = [item.strip().lower() for item in payload.question_types]
    if not normalized_types:
        _error("question_types must not be empty")
    if any(item not in ALLOWED_QUESTION_TYPES for item in normalized_types):
        _error("question_types contains unsupported values")

    deduped_types = []
    seen = set()
    for item in normalized_types:
        if item not in seen:
            seen.add(item)
            deduped_types.append(item)

    collection = get_collection("user_preferences")
    user_id = _user_object_id(current_user_id)
    now = datetime.utcnow()

    existing = collection.find_one({"user_id": user_id})
    created_at = existing.get("created_at") if existing else now

    doc = {
        "user_id": user_id,
        "default_question_count": payload.default_question_count,
        "difficulty": difficulty,
        "question_types": deduped_types,
        "include_dsa": payload.include_dsa,
        "include_system_design": payload.include_system_design,
        "created_at": created_at,
        "updated_at": now,
    }

    collection.update_one({"user_id": user_id}, {"$set": doc}, upsert=True)
    return {
        "default_question_count": doc["default_question_count"],
        "difficulty": doc["difficulty"],
        "question_types": doc["question_types"],
        "include_dsa": doc["include_dsa"],
        "include_system_design": doc["include_system_design"],
        "updated_at": doc["updated_at"],
    }


@router.get("/notifications")
async def get_notifications(current_user_id: str = Depends(get_current_user)):
    collection = get_collection("user_notifications")
    user_id = _user_object_id(current_user_id)

    existing = collection.find_one({"user_id": user_id})
    if not existing:
        doc = {"user_id": user_id, **DEFAULT_NOTIFICATIONS, "updated_at": datetime.utcnow()}
        collection.update_one({"user_id": user_id}, {"$set": doc}, upsert=True)
        existing = doc

    return {
        "email_notifications": bool(existing.get("email_notifications", True)),
        "interview_reminders": bool(existing.get("interview_reminders", True)),
        "weekly_summary": bool(existing.get("weekly_summary", True)),
        "skill_suggestions": bool(existing.get("skill_suggestions", True)),
        "updated_at": existing.get("updated_at"),
    }


@router.put("/notifications")
async def update_notifications(payload: NotificationsRequest, current_user_id: str = Depends(get_current_user)):
    collection = get_collection("user_notifications")
    user_id = _user_object_id(current_user_id)

    doc = {
        "user_id": user_id,
        "email_notifications": bool(payload.email_notifications),
        "interview_reminders": bool(payload.interview_reminders),
        "weekly_summary": bool(payload.weekly_summary),
        "skill_suggestions": bool(payload.skill_suggestions),
        "updated_at": datetime.utcnow(),
    }

    collection.update_one({"user_id": user_id}, {"$set": doc}, upsert=True)
    return {
        "email_notifications": doc["email_notifications"],
        "interview_reminders": doc["interview_reminders"],
        "weekly_summary": doc["weekly_summary"],
        "skill_suggestions": doc["skill_suggestions"],
        "updated_at": doc["updated_at"],
    }


@router.post("/resume")
async def upload_settings_resume(
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user),
):
    if not file.filename:
        _error("resume file is required")

    extension = Path(file.filename).suffix.lower().lstrip(".")
    if extension not in {"pdf", "docx"}:
        _error("Only PDF or DOCX files are allowed")

    content = await file.read()
    if not content:
        _error("Uploaded file is empty")
    if len(content) > MAX_RESUME_SIZE_BYTES:
        _error("File size must be less than or equal to 5MB")

    temp_path = None
    try:
        temp_file = NamedTemporaryFile(delete=False, suffix=f".{extension}")
        temp_file.write(content)
        temp_file.flush()
        temp_file.close()
        temp_path = temp_file.name

        parsed = await extract_resume_text(temp_path, extension)
        parsed = clean_text(parsed)
        skills = _extract_skills(parsed)
    except HTTPException:
        raise
    except Exception as e:
        _error(f"Failed to process resume: {str(e)}", code="processing_error")
    finally:
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink(missing_ok=True)

    resumes_collection = get_collection("resumes")
    user_id = _user_object_id(current_user_id)
    now = datetime.utcnow()

    doc = {
        "user_id": user_id,
        "file_name": file.filename,
        "file_type": extension,
        "extracted_skills": skills,
        "parsed_text": parsed,
        "uploaded_at": now,
        "updated_at": now,
        "is_settings_resume": True,
    }

    resumes_collection.update_one({"user_id": user_id, "is_settings_resume": True}, {"$set": doc}, upsert=True)

    return {
        "file_name": doc["file_name"],
        "extracted_skills": doc["extracted_skills"],
        "uploaded_at": doc["uploaded_at"],
    }


@router.get("/resume")
async def get_settings_resume(current_user_id: str = Depends(get_current_user)):
    resumes_collection = get_collection("resumes")
    resume = resumes_collection.find_one({"user_id": _user_object_id(current_user_id), "is_settings_resume": True})

    if not resume:
        return {"file_name": None, "extracted_skills": [], "uploaded_at": None}

    return {
        "file_name": resume.get("file_name"),
        "extracted_skills": resume.get("extracted_skills", []),
        "uploaded_at": resume.get("uploaded_at"),
    }


@router.delete("/resume")
async def delete_settings_resume(current_user_id: str = Depends(get_current_user)):
    resumes_collection = get_collection("resumes")
    resumes_collection.delete_one({"user_id": _user_object_id(current_user_id), "is_settings_resume": True})
    return {"message": "Resume deleted successfully"}


@router.get("/export-data")
async def export_user_data(current_user_id: str = Depends(get_current_user)):
    user_id = _user_object_id(current_user_id)

    users_collection = get_collection("users")
    interviews_collection = get_collection("interviews")
    intelligence_collection = get_collection("career_intelligence")
    preferences_collection = get_collection("user_preferences")
    notifications_collection = get_collection("user_notifications")
    resumes_collection = get_collection("resumes")

    user = users_collection.find_one({"_id": user_id})
    interviews = list(interviews_collection.find({"user_id": user_id}, sort=[("created_at", -1)]))
    intelligence = intelligence_collection.find_one({"user_id": user_id})
    preferences = preferences_collection.find_one({"user_id": user_id})
    notifications = notifications_collection.find_one({"user_id": user_id})
    resume = resumes_collection.find_one({"user_id": user_id, "is_settings_resume": True})

    def serialize_document(doc):
        if not doc:
            return None
        result = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            else:
                result[key] = value
        return result

    return {
        "user": serialize_document(user),
        "interviews": [serialize_document(item) for item in interviews],
        "career_intelligence": serialize_document(intelligence),
        "preferences": serialize_document(preferences),
        "notifications": serialize_document(notifications),
        "resume": serialize_document(resume),
    }


@router.delete("/account")
async def delete_account(current_user_id: str = Depends(get_current_user)):
    user_id = _user_object_id(current_user_id)

    users_collection = get_collection("users")
    interviews_collection = get_collection("interviews")
    intelligence_collection = get_collection("career_intelligence")
    preferences_collection = get_collection("user_preferences")
    notifications_collection = get_collection("user_notifications")
    resumes_collection = get_collection("resumes")

    users_collection.delete_one({"_id": user_id})
    interviews_collection.delete_many({"user_id": user_id})
    intelligence_collection.delete_many({"user_id": user_id})
    preferences_collection.delete_many({"user_id": user_id})
    notifications_collection.delete_many({"user_id": user_id})
    resumes_collection.delete_many({"user_id": user_id})

    return {"message": "Account deleted permanently"}
