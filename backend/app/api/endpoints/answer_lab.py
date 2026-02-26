"""
Answer Lab API endpoints.
Provides AI-style coaching feedback for a single interview answer.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Literal

router = APIRouter(prefix="/api/answer-lab", tags=["answer-lab"])


class AnswerLabAnalyzeRequest(BaseModel):
    question: str = Field(..., min_length=5)
    answer: str = Field(..., min_length=5)
    type: Literal["Technical", "Behavioral"]


class AnswerLabAnalyzeResponse(BaseModel):
    overall_score: int
    clarity_score: int
    structure_score: int
    technical_depth_score: int
    strengths: List[str]
    weaknesses: List[str]
    improved_answer: str
    star_format_feedback: str


def _score_answer(question: str, answer: str, answer_type: str):
    text = answer.strip()
    word_count = len(text.split())

    clarity_score = 5
    if word_count >= 30:
        clarity_score += 1
    if word_count >= 70:
        clarity_score += 1
    if any(token in text.lower() for token in ["because", "therefore", "so that", "for example"]):
        clarity_score += 1

    structure_score = 5
    sentence_markers = ["first", "second", "finally", "then"]
    if any(marker in text.lower() for marker in sentence_markers):
        structure_score += 1
    if len([s for s in text.replace("\n", ".").split(".") if s.strip()]) >= 3:
        structure_score += 1

    technical_depth_score = 5
    tech_keywords = [
        "api", "database", "cache", "latency", "scalability", "testing",
        "architecture", "complexity", "security", "trade-off"
    ]
    if answer_type == "Technical":
        hit_count = sum(1 for key in tech_keywords if key in text.lower())
        if hit_count >= 2:
            technical_depth_score += 1
        if hit_count >= 4:
            technical_depth_score += 1
    else:
        technical_depth_score = 6

    clarity_score = max(1, min(10, clarity_score))
    structure_score = max(1, min(10, structure_score))
    technical_depth_score = max(1, min(10, technical_depth_score))

    overall = round((clarity_score + structure_score + technical_depth_score) / 3)

    strengths = []
    weaknesses = []

    if clarity_score >= 7:
        strengths.append("Clear explanation")
    else:
        weaknesses.append("Improve clarity with concise phrasing")

    if structure_score >= 7:
        strengths.append("Well-structured response")
    else:
        weaknesses.append("Use stronger structure (opening, reasoning, close)")

    if technical_depth_score >= 7:
        strengths.append("Good technical depth")
    else:
        weaknesses.append("Add deeper technical detail and trade-offs")

    if not strengths:
        strengths.append("Relevant attempt to address the question")

    if not weaknesses:
        weaknesses.append("Add measurable impact to make the answer stronger")

    improved_answer = (
        f"For the question: '{question}', start with a concise summary, then explain your approach "
        f"step-by-step with one practical example and measurable impact. "
        f"Conclude with trade-offs and why your approach is suitable."
    )

    star_feedback = ""
    if answer_type == "Behavioral":
        star_feedback = (
            "Use STAR format explicitly: Situation, Task, Action, and measurable Result "
            "to make your response more compelling."
        )

    return {
        "overall_score": overall,
        "clarity_score": clarity_score,
        "structure_score": structure_score,
        "technical_depth_score": technical_depth_score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improved_answer": improved_answer,
        "star_format_feedback": star_feedback,
    }


@router.post("/analyze", response_model=AnswerLabAnalyzeResponse)
async def analyze_answer(payload: AnswerLabAnalyzeRequest):
    """
    Analyze a user answer and return coaching feedback.
    """
    try:
        return _score_answer(payload.question, payload.answer, payload.type)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze answer: {str(exc)}"
        )
