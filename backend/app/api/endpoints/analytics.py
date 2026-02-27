"""
Analytics API endpoints.
Dashboard data, performance metrics, and insights.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from app.schemas.api import AnalyticsData
from app.services.analytics import get_domain_performance, get_improvement_suggestions
from app.services.career_intelligence import get_user_intelligence
from app.api.dependencies import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=AnalyticsData)
async def get_dashboard(current_user_id: str = Depends(get_current_user)):
    """
    Get dashboard analytics data.
    
    Args:
        current_user_id: Current user ID from token
        
    Returns:
        Analytics data
    """
    
    try:
        analytics = get_user_intelligence(current_user_id)
        
        return AnalyticsData(
            average_score=analytics.get("average_score", 0),
            best_score=max([
                float(item.get("score", 0) or 0)
                for item in analytics.get("trend", [])
            ] or [0]),
            interview_count=analytics.get("completed_interviews", 0),
            domain_performance=analytics.get("domain_performance", {}),
            recent_interviews=analytics.get("recent_interviews", []),
            improvement_trend=analytics.get("trend", [])
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}"
        )


@router.get("/domain/{domain}")
async def get_domain_stats(
    domain: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get performance stats for a specific domain.
    
    Args:
        domain: Domain name
        current_user_id: Current user ID from token
        
    Returns:
        Domain performance data
    """
    
    try:
        stats = await get_domain_performance(current_user_id, domain)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch domain stats: {str(e)}"
        )


@router.get("/suggestions")
async def get_suggestions(current_user_id: str = Depends(get_current_user)):
    """
    Get improvement suggestions based on interview performance.
    
    Args:
        current_user_id: Current user ID from token
        
    Returns:
        List of suggestions
    """
    
    try:
        suggestions = await get_improvement_suggestions(current_user_id)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch suggestions: {str(e)}"
        )


@router.get("/interviews")
async def get_interview_history(current_user_id: str = Depends(get_current_user)):
    """
    Get user's interview history.
    
    Args:
        current_user_id: Current user ID from token
        
    Returns:
        List of interviews
    """
    
    from app.core.database import get_collection
    from bson import ObjectId
    
    interviews_collection = get_collection("interviews")
    
    interviews = list(interviews_collection.find(
        {"user_id": ObjectId(current_user_id)},
        sort=[("created_at", -1)],
        limit=50
    ))
    
    return {
        "count": len(interviews),
        "interviews": [
            {
                "id": str(i["_id"]),
                "job_role": i.get("job_role", ""),
                "domain": i.get("domain", ""),
                "score": i.get("overall_score", 0),
                "status": i.get("status", ""),
                "date": i.get("created_at"),
                "questions_count": len(i.get("questions", []))
            }
            for i in interviews
        ]
    }


@router.get("/full-analytics")
async def get_full_analytics(current_user_id: str = Depends(get_current_user)):
    """
    Get comprehensive analytics data for the dashboard.
    Single endpoint that returns all aggregated data for the analytics page.
    
    Args:
        current_user_id: Current user ID from token
        
    Returns:
        Complete analytics data object
    """
    from app.core.database import get_collection
    from bson import ObjectId
    from datetime import datetime
    
    interviews_collection = get_collection("interviews")
    user_id = ObjectId(current_user_id)
    
    # Get all completed interviews
    completed_interviews = list(interviews_collection.find(
        {"user_id": user_id, "status": "completed"},
        sort=[("created_at", -1)]
    ))
    
    if not completed_interviews:
        return {
            "stats": {
                "total_interviews": 0,
                "completed": 0,
                "average_score": 0,
                "best_score": 0
            },
            "score_trend": [],
            "domain_performance": [],
            "interview_history": [],
            "performance_summary": {
                "total_completed": 0,
                "best_score": 0,
                "worst_score": 0,
                "last_interview_date": None,
                "average_score": 0,
                "improvement_percentage": 0
            },
            "strengths": "Complete more interviews to identify your strengths",
            "improvements": "The system will analyze your weak points after more interviews"
        }
    
    # Calculate stats
    scores = [i.get("overall_score", 0) for i in completed_interviews]
    total_interviews = len(completed_interviews)
    average_score = round(sum(scores) / len(scores), 2) if scores else 0
    best_score = round(max(scores), 2) if scores else 0
    worst_score = round(min(scores), 2) if scores else 0
    
    # Score trend over time (ordered chronologically)
    score_trend = [
        {
            "label": f"Interview {idx + 1}",
            "score": i.get("overall_score", 0),
            "date": i.get("created_at").isoformat() if i.get("created_at") else ""
        }
        for idx, i in enumerate(reversed(completed_interviews))
    ]
    
    # Domain performance
    domain_stats = {}
    for interview in completed_interviews:
        domain = interview.get("domain", "Unknown")
        score = interview.get("overall_score", 0)
        
        if domain not in domain_stats:
            domain_stats[domain] = {"total": 0, "count": 0}
        
        domain_stats[domain]["total"] += score
        domain_stats[domain]["count"] += 1
    
    domain_performance = [
        {
            "name": domain,
            "value": round(stats["total"] / stats["count"], 2)
        }
        for domain, stats in sorted(domain_stats.items())
    ]
    
    # Interview history (limit to 10)
    interview_history = [
        {
            "id": str(i["_id"]),
            "job_role": i.get("job_role", ""),
            "domain": i.get("domain", ""),
            "score": i.get("overall_score", 0),
            "date": i.get("created_at").isoformat() if i.get("created_at") else "",
            "status": _get_status_badge(i.get("overall_score", 0))
        }
        for i in completed_interviews[:10]
    ]
    
    # Performance summary
    last_interview_date = completed_interviews[0].get("created_at") if completed_interviews else None
    first_score = scores[-1] if scores else 0
    last_score = scores[0] if scores else 0
    improvement_percentage = round(((last_score - first_score) / first_score * 100), 2) if first_score > 0 else 0
    
    return {
        "stats": {
            "total_interviews": total_interviews,
            "completed": total_interviews,
            "average_score": average_score,
            "best_score": best_score
        },
        "score_trend": score_trend,
        "domain_performance": domain_performance,
        "interview_history": interview_history,
        "performance_summary": {
            "total_completed": total_interviews,
            "best_score": best_score,
            "worst_score": worst_score,
            "last_interview_date": last_interview_date.isoformat() if last_interview_date else None,
            "average_score": average_score,
            "improvement_percentage": improvement_percentage
        },
        "strengths": _get_strengths_message(domain_performance, average_score),
        "improvements": _get_improvements_message(scores)
    }


def _get_status_badge(score: float) -> str:
    """Determine status badge based on score."""
    if score >= 80:
        return "good"
    elif score >= 60:
        return "needs_improvement"
    else:
        return "poor"


def _get_strengths_message(domain_performance: list, avg_score: float) -> str:
    """Generate strengths message."""
    if not domain_performance:
        return "Complete more interviews to identify your strengths"
    
    best_domain = max(domain_performance, key=lambda x: x["value"])
    return f"You excel in {best_domain['name']} with an average score of {best_domain['value']}%"


def _get_improvements_message(scores: list) -> str:
    """Generate improvements message."""
    if len(scores) < 2:
        return "The system will analyze your weak points after more interviews"
    
    recent_avg = sum(scores[:3]) / len(scores[:3])
    if recent_avg < 60:
        return "Focus on technical accuracy - practice more coding problems"
    elif recent_avg < 70:
        return "Work on communication skills and clarity in your responses"
    else:
        return "Great progress! Continue practicing to maintain consistency"


@router.get("/summary")
async def get_summary(response: Response, current_user_id: str = Depends(get_current_user)):
    """
    Get analytics summary across all interviews for the current user.
    Uses completed interviews for scoring metrics and all interviews for totals.
    """
    try:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return get_user_intelligence(current_user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics summary: {str(e)}"
        )
