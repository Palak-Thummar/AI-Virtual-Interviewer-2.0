"""
Interview history API endpoints.
"""

from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.core.database import get_collection

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


@router.get("")
async def list_interviews(current_user_id: str = Depends(get_current_user)):
    interviews_collection = get_collection("interviews")

    interviews = list(
        interviews_collection.find(
            {"user_id": ObjectId(current_user_id)},
            sort=[("created_at", -1)]
        )
    )

    response = []
    for interview in interviews:
        created_at = interview.get("created_at")
        completed_at = interview.get("completed_at")
        interview_date = completed_at or created_at

        answers = interview.get("answers", [])
        strengths = []
        weaknesses = []
        for answer in answers:
            if not isinstance(answer, dict):
                continue
            strengths.extend(answer.get("strengths", []) or [])
            weaknesses.extend(answer.get("improvements", []) or [])

        unique_strengths = list(dict.fromkeys([s for s in strengths if isinstance(s, str)]))[:4]
        unique_weaknesses = list(dict.fromkeys([w for w in weaknesses if isinstance(w, str)]))[:4]

        skill_breakdown = interview.get("skill_breakdown") or {
            "DSA": 0,
            "System Design": 0,
            "Behavioral": 0,
            "Communication": 0,
        }

        response.append(
            {
                "id": str(interview.get("_id")),
                "role": interview.get("role") or interview.get("job_role", ""),
                "company": interview.get("company", "-") or "-",
                "score": round(float(interview.get("total_score", interview.get("overall_score", 0)) or 0), 2),
                "status": "completed" if interview.get("status") == "completed" else "pending",
                "date": interview_date.strftime("%Y-%m-%d") if isinstance(interview_date, datetime) else "",
                "skill_breakdown": skill_breakdown,
                "strengths": unique_strengths,
                "weaknesses": unique_weaknesses,
            }
        )

    return response
