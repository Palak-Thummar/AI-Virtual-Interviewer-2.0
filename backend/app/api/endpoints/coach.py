"""AI coach conversational endpoint."""

from typing import List, Dict

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAI
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_collection
from app.services.career_intelligence import get_or_create_user_intelligence

router = APIRouter(prefix="/api/coach", tags=["coach"])


class CoachChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: List[Dict[str, str]] = Field(default_factory=list)


@router.post("/chat")
async def coach_chat(payload: CoachChatRequest, current_user_id: str = Depends(get_current_user)):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI coach is not configured")

    users = get_collection("users")
    resumes = get_collection("resumes")
    interviews = get_collection("interviews")

    user = users.find_one({"_id": ObjectId(current_user_id)}) or {}
    resume = resumes.find_one({"user_id": ObjectId(current_user_id)}, sort=[("uploaded_at", -1)]) or {}
    recent_interviews = list(interviews.find({"user_id": ObjectId(current_user_id)}, sort=[("created_at", -1)], limit=5))
    intelligence = get_or_create_user_intelligence(current_user_id)

    context = {
        "name": user.get("name") or user.get("full_name") or "Candidate",
        "role": user.get("primary_role") or "",
        "skills": resume.get("extracted_skills", [])[:20],
        "job_readiness_index": intelligence.get("job_readiness_index", 0),
        "average_score": intelligence.get("average_score", 0),
        "weakest_skill": intelligence.get("weakest_skill", "-"),
        "daily_streak": intelligence.get("daily_streak", 0),
        "recent_scores": [
            float(item.get("score", item.get("total_score", 0)) or 0)
            for item in recent_interviews
            if item.get("status") == "completed"
        ],
    }

    system_prompt = (
        "You are an expert AI Interview Coach for software engineering careers. "
        "Use the candidate context and provide direct, actionable guidance. "
        "Keep responses concise, practical, and tailored to backend/coding interviews. "
        "Always format your response with clear spacing: a short heading, then bullet points, then a 3-step action plan. "
        "Use plain text with line breaks and avoid returning one long paragraph."
    )

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY)

    messages = [{"role": "system", "content": f"{system_prompt}\nContext: {context}"}]
    for item in (payload.history or [])[-10:]:
        role = item.get("role", "user")
        if role not in {"user", "assistant"}:
            continue
        content = item.get("content", "")
        if content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": payload.message})

    try:
        response = client.chat.completions.create(
            model=settings.COACH_MODEL_NAME,
            messages=messages,
            temperature=0.4,
        )
        answer = (response.choices[0].message.content or "").strip()
        return {"reply": answer, "context": context}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Coach service failed: {str(exc)}")
