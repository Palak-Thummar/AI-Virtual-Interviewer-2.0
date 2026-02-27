"""
Career intelligence API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from app.api.dependencies import get_current_user
from app.services.career_intelligence import get_user_intelligence, rebuild_user_intelligence

router = APIRouter(prefix="/api/career-intelligence", tags=["career-intelligence"])


@router.get("")
async def get_career_intelligence(response: Response, current_user_id: str = Depends(get_current_user)):
    try:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return get_user_intelligence(current_user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch career intelligence: {str(e)}"
        )


@router.post("/rebuild")
async def rebuild_career_intelligence(current_user_id: str = Depends(get_current_user)):
    try:
        return rebuild_user_intelligence(current_user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rebuild career intelligence: {str(e)}"
        )
