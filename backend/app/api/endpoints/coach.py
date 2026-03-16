"""AI coach conversational endpoint."""

from typing import List, Dict
import hashlib
import re

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


def _build_fallback_coach_reply(context: Dict[str, object], user_message: str) -> str:
    """Return an offline coaching response tailored to the user's latest prompt."""
    weakest_skill = str(context.get("weakest_skill") or "communication")
    role = str(context.get("role") or "software engineer")
    readiness = float(context.get("job_readiness_index") or 0)
    avg_score = float(context.get("average_score") or 0)
    recent_scores = [float(score or 0) for score in context.get("recent_scores", [])]

    normalized = (user_message or "").strip().lower()
    digest = int(hashlib.sha1(normalized.encode("utf-8")).hexdigest(), 16) if normalized else 0

    if re.search(r"system design|architecture|distributed|scal", normalized):
        focus = "system design"
        priorities = [
            "Define requirements first: scale, latency, consistency, and cost trade-offs.",
            "Use a repeatable framework: API -> data model -> components -> bottlenecks -> mitigations.",
            "Practice drawing 2 alternatives and explain why you chose one.",
        ]
        action_options = [
            "Take one product (chat, ride-sharing, feed) and design it in 35 minutes.",
            "Write one-page design notes before speaking to improve structure.",
            "Revisit one past design and add failure handling plus observability.",
        ]
    elif re.search(r"coding|dsa|algorithm|leetcode|array|tree|graph|dp", normalized):
        focus = "coding rounds"
        priorities = [
            "State brute-force first, then optimize with explicit time and space complexity.",
            "Narrate edge cases before coding (empty input, duplicates, overflow, bounds).",
            "After coding, run two manual dry-runs and one adversarial test.",
        ]
        action_options = [
            "Solve 2 medium problems daily with a 40-minute timer and verbal explanation.",
            "Build a personal pattern sheet: two pointers, sliding window, BFS/DFS, heap, DP.",
            "Re-solve previously failed questions after 72 hours without looking at notes.",
        ]
    elif re.search(r"resume|project|portfolio|experience", normalized):
        focus = "resume storytelling"
        priorities = [
            "Turn each project bullet into problem -> action -> measurable result.",
            "Highlight ownership, constraints, and trade-offs instead of tool lists.",
            "Prepare one deep-dive story for your strongest project.",
        ]
        action_options = [
            "Rewrite your top 3 bullets with numbers and impact statements.",
            "Record a 90-second project walkthrough and remove filler words.",
            "Prepare concise answers for tech stack choices and alternatives considered.",
        ]
    else:
        focus = "behavioral interviews"
        priorities = [
            "Use STAR with strong Action and quantified Result sections.",
            "Lead with the outcome in the first sentence to improve clarity.",
            "Match examples to leadership, ownership, and conflict-resolution themes.",
        ]
        action_options = [
            "Prepare 6 STAR stories mapped to common behavioral themes.",
            "Practice concise 75-second versions, then expand to 2-minute versions.",
            "After each mock, rewrite weak answers into stronger STAR structure.",
        ]

    trend = "stable"
    if len(recent_scores) >= 2:
        trend = "improving" if recent_scores[-1] > recent_scores[0] else "declining"

    step_2_options = [
        f"Do one mock focused on {focus} and capture three mistakes in a log.",
        "Review your mock and convert each mistake into a concrete correction rule.",
        "Repeat the same question set in 48 hours to measure retention.",
    ]
    step_3_options = [
        "Track progress with a simple scorecard: structure, clarity, depth, confidence.",
        "Set a weekly target and review whether your weak area actually moved.",
        "Share one mock with a peer for external feedback on clarity and impact.",
    ]

    action_1 = action_options[digest % len(action_options)]
    action_2 = step_2_options[(digest // 3) % len(step_2_options)]
    action_3 = step_3_options[(digest // 7) % len(step_3_options)]

    return (
        "Offline AI Coach Plan\n\n"
        f"Question focus: {user_message.strip() or 'General improvement'}\n"
        f"You are targeting {role}. Current readiness is {readiness:.1f}/100 with an average interview score of {avg_score:.1f}/10.\n"
        f"Primary improvement area: {weakest_skill}. Recent trend appears {trend}.\n\n"
        "Top priorities\n"
        f"- Focus this week on {focus}.\n"
        f"- {priorities[0]}\n"
        f"- {priorities[1]}\n"
        f"- {priorities[2]}\n\n"
        "3-step action plan\n"
        f"1. {action_1}\n"
        f"2. {action_2}\n"
        f"3. {action_3}"
    )


def _normalize_for_compare(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


@router.post("/chat")
async def coach_chat(payload: CoachChatRequest, current_user_id: str = Depends(get_current_user)):
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
        "Every reply must be specific to the user's latest question and explicitly mention their topic. "
        "Do not repeat previous assistant wording. "
        "Always format your response with clear spacing: a short heading, then bullet points, then a 3-step action plan. "
        "Use plain text with line breaks and avoid returning one long paragraph."
    )

    if not settings.OPENROUTER_API_KEY:
        return {"reply": _build_fallback_coach_reply(context, payload.message), "context": context, "fallback": True}

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
        previous_assistant = ""
        for item in reversed(payload.history or []):
            if item.get("role") == "assistant" and item.get("content"):
                previous_assistant = item.get("content", "")
                break

        response = client.chat.completions.create(
            model=settings.COACH_MODEL_NAME,
            messages=messages,
            temperature=0.65,
            frequency_penalty=0.2,
        )
        answer = (response.choices[0].message.content or "").strip()

        # Guardrail: if provider returns a near-identical answer, force a question-specific fallback.
        if previous_assistant and _normalize_for_compare(answer) == _normalize_for_compare(previous_assistant):
            answer = _build_fallback_coach_reply(context, payload.message)

        return {"reply": answer, "context": context}
    except Exception:
        return {"reply": _build_fallback_coach_reply(context, payload.message), "context": context, "fallback": True}
