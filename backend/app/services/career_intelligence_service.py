"""
Career intelligence aggregation service.
Maintains a single source of truth for dashboard and career intelligence views.
"""

from datetime import datetime
from typing import Dict, List

from bson import ObjectId

from app.core.database import get_collection


SKILL_KEYS = ["DSA", "System Design", "Behavioral", "Communication"]


def _to_object_id(user_id: str | ObjectId) -> ObjectId:
    return user_id if isinstance(user_id, ObjectId) else ObjectId(user_id)


def _to_score(value) -> float:
    try:
        score = float(value or 0)
    except (TypeError, ValueError):
        score = 0.0
    return round(max(0.0, min(100.0, score)), 2)


def _empty_skill_map() -> Dict[str, float]:
    return {skill: 0.0 for skill in SKILL_KEYS}


def _extract_interview_score(interview: Dict) -> float:
    return _to_score(
        interview.get("score", interview.get("total_score", interview.get("overall_score", 0)))
    )


def _extract_skill_scores(interview: Dict) -> Dict[str, float]:
    raw = interview.get("skill_scores") or interview.get("skill_breakdown") or {}
    return {skill: _to_score(raw.get(skill, 0)) for skill in SKILL_KEYS}


def _build_recommendations(skill_averages: Dict[str, float], average_score: float, completed_count: int) -> List[str]:
    if completed_count == 0:
        return ["Complete your first interview to unlock personalized guidance."]

    recommendations: List[str] = []
    if skill_averages.get("DSA", 0) < 70:
        recommendations.append("Practice structured problem solving and explain your approach clearly.")
    if skill_averages.get("System Design", 0) < 70:
        recommendations.append("Strengthen system design fundamentals with scalability trade-off practice.")
    if skill_averages.get("Behavioral", 0) < 70:
        recommendations.append("Use STAR-style examples to improve behavioral interview responses.")
    if skill_averages.get("Communication", 0) < 70:
        recommendations.append("Focus on concise, step-by-step communication during interviews.")
    if average_score >= 80 and not recommendations:
        recommendations.append("Maintain momentum with harder interview sets and company-specific practice.")
    if not recommendations:
        recommendations.append("Keep practicing consistently to improve score stability.")
    return recommendations[:4]


def _serialize_recent_interviews(completed_interviews: List[Dict]) -> List[Dict]:
    items: List[Dict] = []
    for interview in list(reversed(completed_interviews))[:5]:
        date_value = interview.get("completed_at") or interview.get("created_at") or interview.get("updated_at")
        items.append(
            {
                "interview_id": str(interview.get("_id")),
                "role": interview.get("role") or interview.get("job_role") or "",
                "domain": interview.get("domain") or "General",
                "score": _extract_interview_score(interview),
                "date": date_value.strftime("%Y-%m-%d") if date_value else "",
                "status": "completed",
            }
        )
    return items


def _serialize_role_breakdown(completed_interviews: List[Dict]) -> List[Dict]:
    grouped: Dict[str, Dict[str, float]] = {}
    for interview in completed_interviews:
        role = interview.get("role") or interview.get("job_role") or "Unknown"
        grouped.setdefault(role, {"count": 0, "total": 0.0})
        grouped[role]["count"] += 1
        grouped[role]["total"] += _extract_interview_score(interview)

    payload = [
        {
            "role": role,
            "count": int(values["count"]),
            "average_score": round(values["total"] / values["count"], 2),
        }
        for role, values in grouped.items()
        if values["count"] > 0
    ]
    payload.sort(key=lambda item: item["role"])
    return payload


def _serialize_domain_performance(completed_interviews: List[Dict]) -> Dict[str, float]:
    grouped: Dict[str, Dict[str, float]] = {}
    for interview in completed_interviews:
        domain = interview.get("domain") or "General"
        grouped.setdefault(domain, {"count": 0, "total": 0.0})
        grouped[domain]["count"] += 1
        grouped[domain]["total"] += _extract_interview_score(interview)

    return {
        domain: round(values["total"] / values["count"], 2)
        for domain, values in grouped.items()
        if values["count"] > 0
    }


def build_career_intelligence_payload(user_id: str | ObjectId, interviews: List[Dict]) -> Dict:
    user_object_id = _to_object_id(user_id)
    completed_interviews = [item for item in interviews if item.get("status") == "completed"]

    total_interviews = len(interviews)
    completed_count = len(completed_interviews)
    pending_count = total_interviews - completed_count
    completion_rate = round((completed_count / total_interviews) * 100, 2) if total_interviews else 0.0

    scores = [_extract_interview_score(item) for item in completed_interviews]
    average_score = round(sum(scores) / len(scores), 2) if scores else 0.0

    skill_buckets = {skill: [] for skill in SKILL_KEYS}
    for interview in completed_interviews:
        skill_scores = _extract_skill_scores(interview)
        for skill, value in skill_scores.items():
            skill_buckets[skill].append(value)

    skill_averages = {
        skill: round(sum(values) / len(values), 2) if values else 0.0
        for skill, values in skill_buckets.items()
    }

    strongest_skill = "-"
    weakest_skill = "-"
    if completed_count:
        strongest_skill = max(skill_averages, key=skill_averages.get)
        weakest_skill = min(skill_averages, key=skill_averages.get)

    score_trend = []
    for attempt, interview in enumerate(completed_interviews, start=1):
        date_value = interview.get("completed_at") or interview.get("updated_at") or interview.get("created_at")
        score_trend.append(
            {
                "interview_id": str(interview.get("_id")),
                "attempt": attempt,
                "date": date_value.strftime("%Y-%m-%d") if date_value else "",
                "score": _extract_interview_score(interview),
            }
        )

    domain_performance = _serialize_domain_performance(completed_interviews)
    role_breakdown = _serialize_role_breakdown(completed_interviews)
    recent_interviews = _serialize_recent_interviews(completed_interviews)
    recommendations = _build_recommendations(skill_averages, average_score, completed_count)
    updated_at = datetime.utcnow()

    return {
        "user_id": user_object_id,
        "total_interviews": total_interviews,
        "completed_interviews": completed_count,
        "pending_interviews": pending_count,
        "completion_rate": completion_rate,
        "average_score": average_score,
        "role_readiness": average_score,
        "strongest_skill": strongest_skill,
        "weakest_skill": weakest_skill,
        "skill_averages": skill_averages,
        "skill_scores": skill_averages,
        "skill_breakdown": skill_averages,
        "score_trend": score_trend,
        "trend": [{"attempt": item["attempt"], "date": item["date"], "score": item["score"]} for item in score_trend],
        "role_breakdown": role_breakdown,
        "domain_performance": domain_performance,
        "recent_interviews": recent_interviews,
        "recommendations": recommendations,
        "updated_at": updated_at,
    }


def rebuild_user_intelligence(user_id: str | ObjectId) -> Dict:
    interviews_collection = get_collection("interviews")
    intelligence_collection = get_collection("career_intelligence")

    user_object_id = _to_object_id(user_id)
    interviews = list(interviews_collection.find({"user_id": user_object_id}, sort=[("created_at", 1)]))
    payload = build_career_intelligence_payload(user_object_id, interviews)

    intelligence_collection.create_index("user_id", unique=True)
    intelligence_collection.update_one({"user_id": user_object_id}, {"$set": payload}, upsert=True)

    return serialize_career_intelligence(payload)


def serialize_career_intelligence(document: Dict | None) -> Dict:
    if not document:
        empty_skills = _empty_skill_map()
        return {
            "total_interviews": 0,
            "completed_interviews": 0,
            "pending_interviews": 0,
            "completion_rate": 0.0,
            "average_score": 0.0,
            "role_readiness": 0.0,
            "strongest_skill": "-",
            "weakest_skill": "-",
            "skill_averages": empty_skills,
            "skill_scores": empty_skills,
            "skill_breakdown": empty_skills,
            "score_trend": [],
            "trend": [],
            "role_breakdown": [],
            "domain_performance": {},
            "recent_interviews": [],
            "recommendations": ["Complete your first interview to unlock personalized guidance."],
            "updated_at": None,
        }

    skill_scores = document.get("skill_averages") or document.get("skill_scores") or document.get("skill_breakdown") or {}
    normalized_skills = {skill: _to_score(skill_scores.get(skill, 0)) for skill in SKILL_KEYS}
    trend = document.get("score_trend") or document.get("trend") or []
    normalized_trend = [
        {
            "attempt": int(item.get("attempt", index + 1) or index + 1),
            "date": item.get("date", ""),
            "score": _to_score(item.get("score", 0)),
        }
        for index, item in enumerate(trend)
    ]

    updated_at = document.get("updated_at")
    return {
        "total_interviews": int(document.get("total_interviews", 0) or 0),
        "completed_interviews": int(document.get("completed_interviews", 0) or 0),
        "pending_interviews": int(document.get("pending_interviews", 0) or 0),
        "completion_rate": _to_score(document.get("completion_rate", 0)),
        "average_score": _to_score(document.get("average_score", 0)),
        "role_readiness": _to_score(document.get("role_readiness", document.get("average_score", 0))),
        "strongest_skill": document.get("strongest_skill", "-"),
        "weakest_skill": document.get("weakest_skill", "-"),
        "skill_averages": normalized_skills,
        "skill_scores": normalized_skills,
        "skill_breakdown": normalized_skills,
        "score_trend": normalized_trend,
        "trend": normalized_trend,
        "role_breakdown": document.get("role_breakdown", []),
        "domain_performance": document.get("domain_performance", {}),
        "recent_interviews": document.get("recent_interviews", []),
        "recommendations": document.get("recommendations", []),
        "updated_at": updated_at.isoformat() if hasattr(updated_at, "isoformat") else updated_at,
    }


def get_user_intelligence(user_id: str | ObjectId) -> Dict:
    intelligence_collection = get_collection("career_intelligence")
    document = intelligence_collection.find_one({"user_id": _to_object_id(user_id)})
    return serialize_career_intelligence(document)


def get_or_create_user_intelligence(user_id: str | ObjectId) -> Dict:
    document = get_collection("career_intelligence").find_one({"user_id": _to_object_id(user_id)})
    if document:
        return serialize_career_intelligence(document)
    return rebuild_user_intelligence(user_id)