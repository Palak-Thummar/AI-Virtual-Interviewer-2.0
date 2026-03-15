"""Practice Center API endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.services.career_intelligence import get_or_create_user_intelligence

router = APIRouter(prefix="/api/practice-center", tags=["practice-center"])


@router.get("")
async def get_practice_center(current_user_id: str = Depends(get_current_user)):
    intelligence = get_or_create_user_intelligence(current_user_id)
    return {
        "job_readiness_index": intelligence.get("job_readiness_index", 0),
        "areas_to_improve": intelligence.get("practice_recommendations", {}).get("areas_to_improve", []),
        "learning_topics": intelligence.get("practice_recommendations", {}).get("learning_topics", []),
        "recommended_questions": intelligence.get("practice_recommendations", {}).get("recommended_questions", []),
        "practice_interviews": intelligence.get("practice_recommendations", {}).get("practice_interviews", []),
        "achievements": intelligence.get("achievements", []),
        "daily_streak": intelligence.get("daily_streak", 0),
    }
