"""
Analytics service for computing interview statistics and performance metrics.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bson import ObjectId
from app.core.database import get_collection


async def get_user_analytics(user_id: str) -> Dict:
    """
    Get comprehensive analytics for a user.
    
    Args:
        user_id: User ID in MongoDB
        
    Returns:
        Dictionary with analytics data
    """
    
    interviews_collection = get_collection("interviews")
    
    # Convert string ID to ObjectId
    user_object_id = ObjectId(user_id)
    
    # Get all interviews for user
    interviews = list(interviews_collection.find(
        {"user_id": user_object_id, "status": "completed"},
        sort=[("created_at", -1)]
    ))
    
    if not interviews:
        return _get_empty_analytics()
    
    # Calculate metrics
    scores = [i.get("overall_score", 0) for i in interviews]
    average_score = sum(scores) / len(scores) if scores else 0
    best_score = max(scores) if scores else 0
    
    # Domain performance
    domain_stats = {}
    for interview in interviews:
        domain = interview.get("domain", "Unknown")
        score = interview.get("overall_score", 0)
        
        if domain not in domain_stats:
            domain_stats[domain] = {"total": 0, "count": 0}
        
        domain_stats[domain]["total"] += score
        domain_stats[domain]["count"] += 1
    
    domain_performance = {
        domain: round(stats["total"] / stats["count"], 2)
        for domain, stats in domain_stats.items()
    }
    
    # Improvement trend (last 10 interviews)
    recent_interviews = interviews[:10]
    improvement_trend = [
        {
            "date": i.get("created_at").strftime("%Y-%m-%d"),
            "score": i.get("overall_score", 0),
            "domain": i.get("domain", "")
        }
        for i in reversed(recent_interviews)
    ]
    
    return {
        "average_score": round(average_score, 2),
        "best_score": round(best_score, 2),
        "interview_count": len(interviews),
        "domain_performance": domain_performance,
        "recent_interviews": _format_recent_interviews(recent_interviews[:5]),
        "improvement_trend": improvement_trend,
        "last_interview": recent_interviews[0].get("created_at") if recent_interviews else None
    }


async def get_domain_performance(user_id: str, domain: str) -> Dict:
    """
    Get detailed performance metrics for a specific domain.
    
    Args:
        user_id: User ID
        domain: Domain name
        
    Returns:
        Domain-specific performance data
    """
    
    interviews_collection = get_collection("interviews")
    user_object_id = ObjectId(user_id)
    
    domain_interviews = list(interviews_collection.find(
        {
            "user_id": user_object_id,
            "domain": domain,
            "status": "completed"
        }
    ))
    
    if not domain_interviews:
        return {"domain": domain, "interviews": 0, "average_score": 0}
    
    scores = [i.get("overall_score", 0) for i in domain_interviews]
    average_score = sum(scores) / len(scores)
    
    return {
        "domain": domain,
        "interviews": len(domain_interviews),
        "average_score": round(average_score, 2),
        "best_score": max(scores),
        "trend": [s for s in scores],
        "question_average": _calculate_question_performance(domain_interviews)
    }


async def get_improvement_suggestions(user_id: str) -> List[str]:
    """
    Generate improvement suggestions based on user's interview history.
    
    Args:
        user_id: User ID
        
    Returns:
        List of improvement suggestions
    """
    
    interviews_collection = get_collection("interviews")
    user_object_id = ObjectId(user_id)
    
    interviews = list(interviews_collection.find(
        {"user_id": user_object_id, "status": "completed"},
        sort=[("created_at", -1)],
        limit=5
    ))
    
    suggestions = []
    
    # Analyze low scores
    low_score_interviews = [i for i in interviews if i.get("overall_score", 0) < 70]
    if len(low_score_interviews) >= 2:
        suggestions.append("Focus on technical accuracy - practice more coding problems")
    
    # Analyze communication
    interviews_collection = get_collection("interviews")
    high_scores = [i for i in interviews if i.get("overall_score", 0) >= 85]
    
    if high_scores:
        suggestions.append("Great progress! Keep maintaining your current performance level")
    else:
        suggestions.append("Practice mock interviews regularly to build confidence")
    
    # Domain-specific
    domains = [i.get("domain") for i in interviews]
    if domains:
        most_common_domain = max(set(domains), key=domains.count)
        suggestions.append(f"Continue improving in {most_common_domain} domain - you're making progress")
    
    return suggestions[:5]


# ============= HELPER FUNCTIONS =============

def _get_empty_analytics() -> Dict:
    """Return default empty analytics."""
    return {
        "average_score": 0,
        "best_score": 0,
        "interview_count": 0,
        "domain_performance": {},
        "recent_interviews": [],
        "improvement_trend": [],
        "last_interview": None
    }


def _format_recent_interviews(interviews: List) -> List[Dict]:
    """Format recent interviews for response."""
    formatted = []
    
    for interview in interviews:
        formatted.append({
            "interview_id": str(interview.get("_id", "")),
            "job_role": interview.get("job_role", ""),
            "domain": interview.get("domain", ""),
            "score": interview.get("overall_score", 0),
            "date": interview.get("created_at").strftime("%Y-%m-%d") if interview.get("created_at") else "",
            "status": interview.get("status", "")
        })
    
    return formatted


def _calculate_question_performance(interviews: List) -> float:
    """Calculate average performance across all questions."""
    
    all_scores = []
    for interview in interviews:
        answers = interview.get("answers", [])
        for answer in answers:
            if isinstance(answer, dict):
                all_scores.append(answer.get("score", 0))
    
    if not all_scores:
        return 0.0
    
    return round(sum(all_scores) / len(all_scores), 2)


async def get_comparison_with_top_performers(user_id: str) -> Dict:
    """
    Compare user's performance against anonymized top performers.
    
    Args:
        user_id: User ID
        
    Returns:
        Comparison data
    """
    
    # This would typically compare against aggregated anonymized data
    # For MVP, return basic comparison
    return {
        "your_average": 75.0,
        "top_performers_average": 88.0,
        "your_rank": "Top 25%",
        "improvement_needed": 13.0
    }


async def get_analytics_summary(user_id: str) -> Dict:
    """
    Build analytics summary using all interviews, while score aggregations
    are computed from completed interviews only.

    Args:
        user_id: User ID

    Returns:
        Structured analytics summary payload.
    """

    interviews_collection = get_collection("interviews")
    user_object_id = ObjectId(user_id)

    interviews = list(
        interviews_collection.find(
            {"user_id": user_object_id},
            sort=[("created_at", 1)]
        )
    )

    completed_interviews = [i for i in interviews if i.get("status") == "completed"]
    pending_interviews = [i for i in interviews if i.get("status") != "completed"]

    total_interviews = len(interviews)
    completed_count = len(completed_interviews)
    pending_count = len(pending_interviews)

    if completed_count == 0:
        return {
            "total_interviews": total_interviews,
            "completed_interviews": completed_count,
            "pending_interviews": pending_count,
            "average_score": 0,
            "role_readiness": 0,
            "skill_breakdown": {
                "DSA": 0,
                "System Design": 0,
                "Behavioral": 0,
                "Communication": 0,
            },
            "strongest_skill": "-",
            "weakest_skill": "-",
            "trend": [],
            "recommendations": [
                "Complete an interview to unlock personalized recommendations"
            ],
        }

    completed_scores = [float(i.get("overall_score", 0) or 0) for i in completed_interviews]
    average_score = round(sum(completed_scores) / completed_count, 2)
    role_readiness = round(average_score, 2)

    skill_buckets = {
        "DSA": [],
        "System Design": [],
        "Behavioral": [],
        "Communication": [],
    }

    for interview in completed_interviews:
        interview_score = float(interview.get("overall_score", 0) or 0)
        domain = (interview.get("domain") or "").lower()

        if "data" in domain or "dsa" in domain or "algorithm" in domain:
            skill_buckets["DSA"].append(interview_score)
        elif "system" in domain or "backend" in domain or "devops" in domain:
            skill_buckets["System Design"].append(interview_score)
        elif "behavior" in domain or "hr" in domain:
            skill_buckets["Behavioral"].append(interview_score)
        elif "frontend" in domain or "mobile" in domain or "communication" in domain:
            skill_buckets["Communication"].append(interview_score)
        else:
            skill_buckets["Communication"].append(interview_score)

    skill_breakdown = {
        skill: round(sum(values) / len(values), 2) if values else 0
        for skill, values in skill_buckets.items()
    }

    strongest_skill = max(skill_breakdown, key=skill_breakdown.get)
    weakest_skill = min(skill_breakdown, key=skill_breakdown.get)

    trend = [
        {
            "attempt": index + 1,
            "score": round(float(interview.get("overall_score", 0) or 0), 2),
        }
        for index, interview in enumerate(completed_interviews)
    ]

    recommendations = []
    if skill_breakdown["System Design"] < 70:
        recommendations.append("Improve system design fundamentals")
    if skill_breakdown["DSA"] < 70:
        recommendations.append("Practice DSA problem solving regularly")
    if average_score < 75:
        recommendations.append("Practice mock interviews with timed answers")
    if not recommendations:
        recommendations.append("Maintain consistency with advanced interview sets")

    return {
        "total_interviews": total_interviews,
        "completed_interviews": completed_count,
        "pending_interviews": pending_count,
        "average_score": average_score,
        "role_readiness": role_readiness,
        "skill_breakdown": skill_breakdown,
        "strongest_skill": strongest_skill,
        "weakest_skill": weakest_skill,
        "trend": trend,
        "recommendations": recommendations,
    }
