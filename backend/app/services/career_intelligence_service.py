"""
Career intelligence aggregation service.
Maintains a single source of truth for dashboard and career intelligence views.
"""

from datetime import datetime
from typing import Dict, List

from bson import ObjectId

from app.core.database import get_collection
from app.services.notification_service import create_notification


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


def _build_skill_progression(completed_interviews: List[Dict]) -> List[Dict]:
    progression = []
    for attempt, interview in enumerate(completed_interviews, start=1):
        date_value = interview.get("completed_at") or interview.get("created_at") or interview.get("updated_at")
        scores = _extract_skill_scores(interview)
        progression.append(
            {
                "attempt": attempt,
                "date": date_value.strftime("%Y-%m-%d") if date_value else "",
                **scores,
            }
        )
    return progression


def _build_difficulty_trend(completed_interviews: List[Dict]) -> List[Dict]:
    trend = []
    for attempt, interview in enumerate(completed_interviews, start=1):
        trend.append(
            {
                "attempt": attempt,
                "difficulty": interview.get("difficulty") or "Medium",
                "score": _extract_interview_score(interview),
            }
        )
    return trend


def _calculate_streak(completed_interviews: List[Dict]) -> int:
    days = set()
    for interview in completed_interviews:
        completed_at = interview.get("completed_at") or interview.get("updated_at") or interview.get("created_at")
        if completed_at and hasattr(completed_at, "date"):
            days.add(completed_at.date())
    if not days:
        return 0

    streak = 0
    cursor = datetime.utcnow().date()
    while cursor in days:
        streak += 1
        cursor = cursor.fromordinal(cursor.toordinal() - 1)

    if streak == 0:
        yesterday = datetime.utcnow().date().fromordinal(datetime.utcnow().date().toordinal() - 1)
        cursor = yesterday
        while cursor in days:
            streak += 1
            cursor = cursor.fromordinal(cursor.toordinal() - 1)
    return streak


def _build_achievements(completed_count: int, highest_score: float, streak: int) -> List[Dict]:
    badges = []
    if completed_count >= 1:
        badges.append({"key": "first_interview", "title": "First Interview", "unlocked": True})
    if completed_count >= 5:
        badges.append({"key": "five_interviews", "title": "5 Interviews Completed", "unlocked": True})
    if highest_score >= 90:
        badges.append({"key": "score_90", "title": "Score Above 90", "unlocked": True})
    if streak >= 7:
        badges.append({"key": "streak_7", "title": "7 Day Practice Streak", "unlocked": True})
    return badges


def _build_practice_recommendations(skill_averages: Dict[str, float], weakest_skill: str, role_breakdown: List[Dict]) -> Dict:
    low_skills = [skill for skill, score in skill_averages.items() if score < 70]
    skill_to_topics = {
        "System Design": ["Scalability patterns", "Caching and queues", "Database sharding"],
        "DSA": ["Sliding window", "Graphs and BFS/DFS", "Dynamic programming"],
        "Behavioral": ["STAR framework", "Conflict resolution stories", "Leadership examples"],
        "Communication": ["Structured thinking", "Concise articulation", "Trade-off explanation"],
    }

    topics = []
    questions = []
    for skill in low_skills[:2]:
        topics.extend(skill_to_topics.get(skill, []))
        questions.append(f"Practice {skill} interview for 30 minutes")

    role_targets = [item.get("role") for item in role_breakdown[:2] if item.get("role")]
    recommended_interviews = role_targets or ["Backend Developer", "System Design Round"]

    return {
        "areas_to_improve": low_skills or ([weakest_skill] if weakest_skill and weakest_skill != "-" else []),
        "learning_topics": topics[:6],
        "recommended_questions": questions[:6],
        "practice_interviews": recommended_interviews,
    }


def _calculate_job_readiness_index(average_score: float, skill_averages: Dict[str, float], avg_ats: float, completed_count: int) -> float:
    skill_coverage = round((sum(skill_averages.values()) / (len(SKILL_KEYS) * 100)) * 100, 2) if SKILL_KEYS else 0.0
    interview_depth = min(100.0, completed_count * 10.0)
    jri = (average_score * 0.45) + (skill_coverage * 0.25) + (avg_ats * 0.2) + (interview_depth * 0.1)
    return round(max(0.0, min(100.0, jri)), 2)


def build_career_intelligence_payload(user_id: str | ObjectId, interviews: List[Dict]) -> Dict:
    user_object_id = _to_object_id(user_id)
    completed_interviews = [item for item in interviews if item.get("status") == "completed"]

    total_interviews = len(interviews)
    completed_count = len(completed_interviews)
    pending_count = total_interviews - completed_count
    completion_rate = round((completed_count / total_interviews) * 100, 2) if total_interviews else 0.0

    scores = [_extract_interview_score(item) for item in completed_interviews]
    average_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    highest_score = round(max(scores), 2) if scores else 0.0

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
    skill_progression = _build_skill_progression(completed_interviews)
    difficulty_trend = _build_difficulty_trend(completed_interviews)

    ats_scores = [
        _to_score((item.get("skill_match") or {}).get("ats_score", 0))
        for item in completed_interviews
    ]
    avg_ats_score = round(sum(ats_scores) / len(ats_scores), 2) if ats_scores else 0.0

    job_readiness_index = _calculate_job_readiness_index(average_score, skill_averages, avg_ats_score, completed_count)
    streak = _calculate_streak(completed_interviews)
    achievements = _build_achievements(completed_count, highest_score, streak)
    recommendations_detail = _build_practice_recommendations(skill_averages, weakest_skill, role_breakdown)
    recommendations = _build_recommendations(skill_averages, average_score, completed_count)
    updated_at = datetime.utcnow()

    return {
        "user_id": user_object_id,
        "total_interviews": total_interviews,
        "completed_interviews": completed_count,
        "pending_interviews": pending_count,
        "completion_rate": completion_rate,
        "average_score": average_score,
        "highest_score": highest_score,
        "role_readiness": average_score,
        "job_readiness_index": job_readiness_index,
        "strongest_skill": strongest_skill,
        "weakest_skill": weakest_skill,
        "skill_averages": skill_averages,
        "skill_scores": skill_averages,
        "skill_breakdown": skill_averages,
        "score_trend": score_trend,
        "trend": [{"attempt": item["attempt"], "date": item["date"], "score": item["score"]} for item in score_trend],
        "role_breakdown": role_breakdown,
        "domain_performance": domain_performance,
        "skill_progression": skill_progression,
        "difficulty_trend": difficulty_trend,
        "weak_skill_radar": [{"skill": skill, "value": score} for skill, score in skill_averages.items()],
        "recent_interviews": recent_interviews,
        "recommendations": recommendations,
        "practice_recommendations": recommendations_detail,
        "daily_streak": streak,
        "total_interviews_count": total_interviews,
        "achievements": achievements,
        "avg_resume_match": avg_ats_score,
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

    weakest_skill = payload.get("weakest_skill", "-")
    completed_count = int(payload.get("completed_interviews", 0) or 0)
    weakest_score = float((payload.get("skill_averages") or {}).get(weakest_skill, 0) or 0)
    if completed_count > 0 and weakest_skill != "-" and weakest_score < 70:
        try:
            create_notification(
                user_id=str(user_object_id),
                notification_type="SKILL_SUGGESTION",
                title="Skill Improvement Needed",
                message=f"Your weakest skill is {weakest_skill}. Practice recommended.",
                metadata={"weakest_skill": weakest_skill, "weakest_score": weakest_score},
            )
        except Exception:
            # Intelligence rebuild should continue even if notification storage is unavailable.
            pass

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
            "highest_score": 0.0,
            "role_readiness": 0.0,
            "job_readiness_index": 0.0,
            "strongest_skill": "-",
            "weakest_skill": "-",
            "skill_averages": empty_skills,
            "skill_scores": empty_skills,
            "skill_breakdown": empty_skills,
            "score_trend": [],
            "trend": [],
            "role_breakdown": [],
            "domain_performance": {},
            "skill_progression": [],
            "difficulty_trend": [],
            "weak_skill_radar": [],
            "recent_interviews": [],
            "recommendations": ["Complete your first interview to unlock personalized guidance."],
            "practice_recommendations": {
                "areas_to_improve": [],
                "learning_topics": [],
                "recommended_questions": [],
                "practice_interviews": [],
            },
            "daily_streak": 0,
            "total_interviews_count": 0,
            "achievements": [],
            "avg_resume_match": 0.0,
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
        "highest_score": _to_score(document.get("highest_score", 0)),
        "role_readiness": _to_score(document.get("role_readiness", document.get("average_score", 0))),
        "job_readiness_index": _to_score(document.get("job_readiness_index", document.get("average_score", 0))),
        "strongest_skill": document.get("strongest_skill", "-"),
        "weakest_skill": document.get("weakest_skill", "-"),
        "skill_averages": normalized_skills,
        "skill_scores": normalized_skills,
        "skill_breakdown": normalized_skills,
        "score_trend": normalized_trend,
        "trend": normalized_trend,
        "role_breakdown": document.get("role_breakdown", []),
        "domain_performance": document.get("domain_performance", {}),
        "skill_progression": document.get("skill_progression", []),
        "difficulty_trend": document.get("difficulty_trend", []),
        "weak_skill_radar": document.get("weak_skill_radar", []),
        "recent_interviews": document.get("recent_interviews", []),
        "recommendations": document.get("recommendations", []),
        "practice_recommendations": document.get("practice_recommendations", {
            "areas_to_improve": [],
            "learning_topics": [],
            "recommended_questions": [],
            "practice_interviews": [],
        }),
        "daily_streak": int(document.get("daily_streak", 0) or 0),
        "total_interviews_count": int(document.get("total_interviews_count", 0) or 0),
        "achievements": document.get("achievements", []),
        "avg_resume_match": _to_score(document.get("avg_resume_match", 0)),
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