"""
Career intelligence aggregation and integrity service.
"""

from datetime import datetime
from typing import Dict, List
from bson import ObjectId
from app.core.database import get_collection


REQUIRED_SKILLS = ["DSA", "System Design", "Behavioral", "Communication"]


def _to_object_id(user_id: str) -> ObjectId:
    return user_id if isinstance(user_id, ObjectId) else ObjectId(user_id)


def _to_score(value) -> float:
    try:
        score = float(value or 0)
    except (TypeError, ValueError):
        score = 0
    return max(0.0, min(100.0, round(score, 2)))


def _extract_skill_scores(interview: Dict) -> Dict[str, float]:
    raw = interview.get("skill_scores") or interview.get("skill_breakdown") or {}
    normalized = {}
    for skill in REQUIRED_SKILLS:
        normalized[skill] = _to_score(raw.get(skill, 0))
    return normalized


def _extract_total_score(interview: Dict) -> float:
    return _to_score(interview.get("total_score", interview.get("overall_score", 0)))


def _validate_intelligence(payload: Dict):
    total_interviews = int(payload.get("total_interviews", 0))
    if total_interviews < 0:
        raise ValueError("total_interviews must be >= 0")

    average_score = _to_score(payload.get("average_score", 0))
    if average_score < 0 or average_score > 100:
        raise ValueError("average_score must be between 0 and 100")

    skill_scores = payload.get("skill_scores", {}) or {}
    for skill in REQUIRED_SKILLS:
        skill_scores[skill] = _to_score(skill_scores.get(skill, 0))

    trend = payload.get("score_trend", []) or []
    ids = [item.get("interview_id") for item in trend if item.get("interview_id")]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate entries in score_trend")


def rebuild_user_intelligence(user_id: str) -> Dict:
    interviews_collection = get_collection("interviews")
    intelligence_collection = get_collection("career_intelligence")

    user_object_id = _to_object_id(user_id)

    interviews = list(
        interviews_collection.find(
            {"user_id": user_object_id},
            sort=[("created_at", 1)]
        )
    )

    completed_interviews = [item for item in interviews if item.get("status") == "completed"]
    total_interviews = len(interviews)
    completed_count = len(completed_interviews)
    pending_count = total_interviews - completed_count
    completion_rate = round((completed_count / total_interviews) * 100, 2) if total_interviews else 0

    score_values = [_extract_total_score(item) for item in completed_interviews]
    average_score = round(sum(score_values) / len(score_values), 2) if score_values else 0

    skill_buckets = {skill: [] for skill in REQUIRED_SKILLS}
    for interview in completed_interviews:
        skill_scores = _extract_skill_scores(interview)
        for skill, value in skill_scores.items():
            skill_buckets[skill].append(value)

    aggregated_skill_scores = {
        skill: round(sum(values) / len(values), 2) if values else 0
        for skill, values in skill_buckets.items()
    }

    strongest_skill = max(aggregated_skill_scores, key=aggregated_skill_scores.get) if completed_count else "-"
    weakest_skill = min(aggregated_skill_scores, key=aggregated_skill_scores.get) if completed_count else "-"

    trend = []
    for index, interview in enumerate(completed_interviews, start=1):
        trend_date = interview.get("completed_at") or interview.get("updated_at") or interview.get("created_at")
        trend.append(
            {
                "interview_id": str(interview.get("_id")),
                "attempt": index,
                "date": trend_date.strftime("%Y-%m-%d") if trend_date else "",
                "score": _extract_total_score(interview),
            }
        )

    role_stats = {}
    for interview in completed_interviews:
        role = interview.get("role") or interview.get("job_role") or "Unknown"
        score = _extract_total_score(interview)
        if role not in role_stats:
            role_stats[role] = {"count": 0, "total": 0}
        role_stats[role]["count"] += 1
        role_stats[role]["total"] += score

    role_breakdown = [
        {
            "role": role,
            "count": stats["count"],
            "average_score": round(stats["total"] / stats["count"], 2),
        }
        for role, stats in role_stats.items()
    ]
    role_breakdown.sort(key=lambda item: item["role"])

    recommendations = []
    if aggregated_skill_scores["System Design"] < 70:
        recommendations.append("Improve system design fundamentals")
    if aggregated_skill_scores["DSA"] < 70:
        recommendations.append("Practice DSA problem solving regularly")
    if average_score < 75:
        recommendations.append("Practice timed mock interviews to improve consistency")
    if not recommendations:
        recommendations.append("Maintain consistency with advanced interview sets")

    payload = {
        "user_id": user_object_id,
        "total_interviews": total_interviews,
        "completed_interviews": completed_count,
        "pending_interviews": pending_count,
        "completion_rate": completion_rate,
        "average_score": average_score,
        "strongest_skill": strongest_skill,
        "weakest_skill": weakest_skill,
        "skill_scores": aggregated_skill_scores,
        "score_trend": trend,
        "role_breakdown": role_breakdown,
        "updated_at": datetime.utcnow(),
        "recommendations": recommendations,
    }

    _validate_intelligence(payload)

    intelligence_collection.create_index("user_id", unique=True)
    intelligence_collection.update_one({"user_id": user_object_id}, {"$set": payload}, upsert=True)

    return {
        "total_interviews": total_interviews,
        "completed_interviews": completed_count,
        "pending_interviews": pending_count,
        "completion_rate": completion_rate,
        "average_score": average_score,
        "role_readiness": average_score,
        "strongest_skill": strongest_skill,
        "weakest_skill": weakest_skill,
        "skill_breakdown": aggregated_skill_scores,
        "trend": [{"attempt": item["attempt"], "score": item["score"], "date": item["date"]} for item in trend],
        "role_breakdown": role_breakdown,
        "recommendations": recommendations,
        "updated_at": payload["updated_at"].isoformat(),
    }


def get_or_create_user_intelligence(user_id: str) -> Dict:
    intelligence_collection = get_collection("career_intelligence")
    user_object_id = _to_object_id(user_id)

    intelligence = intelligence_collection.find_one({"user_id": user_object_id})
    if not intelligence:
        return rebuild_user_intelligence(user_id)

    skill_scores = intelligence.get("skill_scores") or {}
    trend = intelligence.get("score_trend") or []

    return {
        "total_interviews": int(intelligence.get("total_interviews", 0) or 0),
        "completed_interviews": int(intelligence.get("completed_interviews", 0) or 0),
        "pending_interviews": int(intelligence.get("pending_interviews", 0) or 0),
        "completion_rate": _to_score(intelligence.get("completion_rate", 0)),
        "average_score": _to_score(intelligence.get("average_score", 0)),
        "role_readiness": _to_score(intelligence.get("average_score", 0)),
        "strongest_skill": intelligence.get("strongest_skill", "-"),
        "weakest_skill": intelligence.get("weakest_skill", "-"),
        "skill_breakdown": {skill: _to_score(skill_scores.get(skill, 0)) for skill in REQUIRED_SKILLS},
        "trend": [
            {
                "attempt": int(item.get("attempt", idx + 1) or (idx + 1)),
                "score": _to_score(item.get("score", 0)),
                "date": item.get("date", ""),
            }
            for idx, item in enumerate(trend)
        ],
        "role_breakdown": intelligence.get("role_breakdown", []),
        "recommendations": intelligence.get("recommendations", []),
        "updated_at": intelligence.get("updated_at").isoformat() if intelligence.get("updated_at") else None,
    }
