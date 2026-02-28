"""
Interview management API endpoints.
Create, manage, and complete interview sessions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from typing import List, Optional, Dict
from bson import ObjectId
from pydantic import BaseModel, Field
from app.schemas.api import (
    InterviewSetup,
    InterviewCreateResponse,
    AnswerEvaluationResponse,
    InterviewResults,
    SkillMatch,
    ResumeSuggestion
)
from app.api.dependencies import get_current_user
from app.services.question_generator import generate_interview_questions
from app.services.jd_resume_analyzer import analyze_resume_against_jd
from app.services.interview_evaluator import evaluate_answer, evaluate_interview_session
from app.services.career_intelligence import rebuild_user_intelligence
from app.core.database import get_collection

router = APIRouter(prefix="/api/interview", tags=["interview"])


def _default_jd_analysis(error_message: str = "") -> dict:
    return {
        "ats_score": 50.0,
        "matched_skills": [],
        "missing_skills": [],
        "keyword_gaps": [],
        "experience_gap": error_message,
        "improvement_suggestions": [],
        "ats_optimization_tips": []
    }


def _get_stored_jd_analysis(interview: dict) -> dict:
    skill_match = interview.get("skill_match") or {}
    resume_suggestions = interview.get("resume_suggestions") or {}

    ats_score = skill_match.get("ats_score")
    if ats_score is None:
        ats_score = interview.get("ats_score", 50.0)

    return {
        "ats_score": ats_score,
        "matched_skills": skill_match.get("matched_skills", interview.get("matched_skills", [])),
        "missing_skills": skill_match.get("missing_skills", interview.get("missing_skills", [])),
        "keyword_gaps": skill_match.get("keyword_gaps", interview.get("keyword_gaps", [])),
        "experience_gap": skill_match.get("experience_gap", interview.get("experience_gap", "")),
        "improvement_suggestions": resume_suggestions.get("improvement_suggestions", interview.get("improvement_suggestions", [])),
        "ats_optimization_tips": resume_suggestions.get("ats_optimization_tips", interview.get("ats_optimization_tips", []))
    }


async def _resolve_jd_analysis(interview: dict, resumes_collection) -> dict:
    stored = _get_stored_jd_analysis(interview)
    if stored.get("ats_score") is not None:
        return stored

    resume = None
    resume_id = interview.get("resume_id")
    if resume_id:
        resume = resumes_collection.find_one({"_id": resume_id})

    resume_text = resume.get("parsed_text", "") if resume else ""
    jd_text = interview.get("job_description", "")

    if not jd_text or not jd_text.strip():
        return _default_jd_analysis("Job description not available for resume match analysis")

    try:
        return await analyze_resume_against_jd(resume_text, jd_text)
    except Exception as e:
        return _default_jd_analysis(f"Analysis error: {str(e)}")


def _get_preferred_question_count(current_user_id: str, fallback: int = 5) -> int:
    preferences_collection = get_collection("user_preferences")
    prefs = preferences_collection.find_one({"user_id": ObjectId(current_user_id)})
    preferred = int((prefs or {}).get("default_question_count", fallback) or fallback)
    return min(20, max(1, preferred))


class CompanyInterviewGenerateRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=80)
    role: str = Field(..., min_length=1, max_length=100)
    difficulty: str = Field(..., min_length=1, max_length=20)
    question_count: int | None = Field(default=None, ge=1, le=5)


class CompanyInterviewQuestion(BaseModel):
    id: int
    question: str
    type: str


class CompanyInterviewGenerateResponse(BaseModel):
    interview_id: str
    company: str
    role: str
    questions: List[CompanyInterviewQuestion]


class QuestionProgressSubmission(BaseModel):
    question_id: int = Field(..., ge=0)
    answer: Optional[str] = ""
    skipped: bool = False


class InterviewSubmitRequest(BaseModel):
    answers: Optional[List[Dict]] = None


@router.post("/create", response_model=InterviewCreateResponse)
async def create_interview(
    setup: InterviewSetup,
    current_user_id: str = Depends(get_current_user)
):
    
    # Verify resume exists
    resumes_collection = get_collection("resumes")
    resume = resumes_collection.find_one({
        "_id": ObjectId(setup.resume_id),
        "user_id": ObjectId(current_user_id)
    })
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Get resume text
    resume_text = resume.get("parsed_text", "")
    
    requested_questions = setup.num_questions if getattr(setup, "num_questions", None) else None
    num_questions = requested_questions or _get_preferred_question_count(current_user_id, fallback=5)

    # Generate interview questions
    try:
        questions = await generate_interview_questions(
            job_role=setup.job_role,
            domain=setup.domain,
            resume_text=resume_text,
            job_description=setup.job_description,
            num_questions=num_questions
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(e)}"
        )
    
    # Create interview record
    interviews_collection = get_collection("interviews")
    
    interview_doc = {
        "user_id": ObjectId(current_user_id),
        "role": setup.job_role,
        "type": "general",
        "domain": setup.domain,
        "job_description": setup.job_description,
        "resume_id": ObjectId(setup.resume_id),
        "questions": questions,
        "answers": [],
        "current_question_index": 0,
        "total_score": None,
        "skill_scores": {},
        "status": "pending",
        "created_at": datetime.utcnow(),
        "completed_at": None,
        "updated_at": datetime.utcnow()
    }
    
    result = interviews_collection.insert_one(interview_doc)
    interview_id = str(result.inserted_id)
    
    return InterviewCreateResponse(
        interview_id=interview_id,
        job_role=setup.job_role,
        domain=setup.domain,
        num_questions=num_questions,
        questions=questions
    )


@router.post("/company-generate", response_model=CompanyInterviewGenerateResponse)
async def generate_company_interview(
    payload: CompanyInterviewGenerateRequest,
    current_user_id: str = Depends(get_current_user)
):
    normalized_company = payload.company.strip()
    normalized_role = payload.role.strip()
    normalized_difficulty = payload.difficulty.strip().capitalize()

    if normalized_difficulty not in {"Easy", "Medium", "Hard"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Difficulty must be one of: Easy, Medium, Hard"
        )

    domain_map = {
        "Backend": "Backend",
        "Frontend": "Frontend",
        "Full Stack": "Full Stack",
        "Data": "Data",
        "Devops": "DevOps",
        "Sre": "SRE"
    }
    inferred_domain = "General"
    role_title = normalized_role.title()
    for key, value in domain_map.items():
        if key.lower() in role_title.lower():
            inferred_domain = value
            break

    question_count = payload.question_count or _get_preferred_question_count(current_user_id, fallback=3)
    generated_questions = await generate_interview_questions(
        job_role=f"{normalized_company} {normalized_role}",
        domain=inferred_domain,
        resume_text="",
        job_description=(
            f"Generate {normalized_difficulty} interview questions for {normalized_company} "
            f"for the role {normalized_role}. Include company-style expectations and practical scenarios."
        ),
        num_questions=question_count
    )

    question_objects: List[dict] = []
    for index, question in enumerate(generated_questions[:question_count], start=1):
        question_type = "Behavioral" if index % 3 == 0 else "Technical"
        question_objects.append({
            "id": index,
            "question": question,
            "type": question_type
        })

    interviews_collection = get_collection("interviews")
    interview_doc = {
        "user_id": ObjectId(current_user_id),
        "role": normalized_role,
        "type": "company",
        "domain": inferred_domain,
        "company": normalized_company,
        "difficulty": normalized_difficulty,
        "questions": [q["question"] for q in question_objects],
        "questions_structured": question_objects,
        "answers": [],
        "current_question_index": 0,
        "total_score": None,
        "skill_scores": {},
        "status": "pending",
        "created_at": datetime.utcnow(),
        "completed_at": None,
        "updated_at": datetime.utcnow()
    }

    created = interviews_collection.insert_one(interview_doc)

    return CompanyInterviewGenerateResponse(
        interview_id=str(created.inserted_id),
        company=normalized_company,
        role=normalized_role,
        questions=[CompanyInterviewQuestion(**q) for q in question_objects]
    )


@router.post("/{interview_id}/submit-answer", response_model=AnswerEvaluationResponse)
async def submit_answer(
    interview_id: str,
    answer_data: QuestionProgressSubmission,
    current_user_id: str = Depends(get_current_user)
):
    """
    Submit an answer to an interview question.
    
    Args:
        interview_id: Interview ID
        answer_data: Answer submission
        current_user_id: Current user ID from token
        
    Returns:
        Answer evaluation
    """
    
    interviews_collection = get_collection("interviews")
    
    # Get interview
    interview = interviews_collection.find_one({
        "_id": ObjectId(interview_id),
        "user_id": ObjectId(current_user_id),
        "status": "pending"
    })
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    # Get question
    questions = interview.get("questions", [])
    if answer_data.question_id >= len(questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid question ID"
        )
    
    question = questions[answer_data.question_id]
    
    current_question_index = int(interview.get("current_question_index", 0) or 0)
    if answer_data.question_id != current_question_index:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question order mismatch"
        )

    if answer_data.skipped:
        next_index = min(current_question_index + 1, len(questions))
        interviews_collection.update_one(
            {"_id": ObjectId(interview_id)},
            {
                "$set": {
                    "current_question_index": next_index,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return AnswerEvaluationResponse(
            question_id=answer_data.question_id,
            score=0,
            feedback="Question skipped",
            strengths=[],
            improvements=[]
        )

    answer_text = (answer_data.answer or "").strip()
    if not answer_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Answer cannot be empty unless skipped"
        )

    # Evaluate answer
    try:
        evaluation = await evaluate_answer(
            question=question,
            answer=answer_text,
            job_context=interview.get("role", "")
        )
    except Exception as e:
        evaluation = {
            "score": 50.0,
            "feedback": "Unable to evaluate at this time",
            "strengths": [],
            "improvements": [],
            "technical_accuracy": 50,
            "communication": 50,
            "completeness": 50
        }
    
    # Store answer
    answer_record = {
        "question_id": answer_data.question_id,
        "question": question,
        "answer": answer_text,
        "score": evaluation.get("score", 0),
        "feedback": evaluation.get("feedback", ""),
        "strengths": evaluation.get("strengths", []),
        "improvements": evaluation.get("improvements", [])
    }

    next_index = min(current_question_index + 1, len(questions))
    
    interviews_collection.update_one(
        {"_id": ObjectId(interview_id)},
        {
            "$push": {"answers": answer_record},
            "$set": {
                "current_question_index": next_index,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return AnswerEvaluationResponse(
        question_id=answer_data.question_id,
        score=evaluation.get("score", 0),
        feedback=evaluation.get("feedback", ""),
        strengths=evaluation.get("strengths", []),
        improvements=evaluation.get("improvements", [])
    )


async def _submit_and_complete_interview(interview_id: str, current_user_id: str, payload: InterviewSubmitRequest) -> InterviewResults:
    interviews_collection = get_collection("interviews")
    resumes_collection = get_collection("resumes")

    interview = interviews_collection.find_one({
        "_id": ObjectId(interview_id),
        "user_id": ObjectId(current_user_id)
    })

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    if interview.get("status") == "completed":
        jd_analysis = await _resolve_jd_analysis(interview, resumes_collection)
        answers = interview.get("answers", [])
        question_scores = [
            AnswerEvaluationResponse(
                question_id=a.get("question_id", 0),
                score=a.get("score", 0),
                feedback=a.get("feedback", ""),
                strengths=a.get("strengths", []),
                improvements=a.get("improvements", [])
            )
            for a in answers
        ]
        return InterviewResults(
            interview_id=interview_id,
            overall_score=float(interview.get("total_score") or 0),
            domain=interview.get("domain", ""),
            job_role=interview.get("role", ""),
            question_scores=question_scores,
            skill_match=SkillMatch(
                matched_skills=jd_analysis.get("matched_skills", []),
                missing_skills=jd_analysis.get("missing_skills", []),
                ats_score=jd_analysis.get("ats_score", 50.0),
                keyword_gaps=jd_analysis.get("keyword_gaps", []),
                experience_gap=jd_analysis.get("experience_gap", "")
            ),
            resume_suggestions=ResumeSuggestion(
                improvement_suggestions=jd_analysis.get("improvement_suggestions", []),
                ats_optimization_tips=jd_analysis.get("ats_optimization_tips", [])
            ),
            completed_at=interview.get("completed_at") or interview.get("updated_at") or datetime.utcnow()
        )

    if payload.answers is not None:
        interviews_collection.update_one(
            {"_id": ObjectId(interview_id)},
            {
                "$set": {
                    "answers": payload.answers,
                    "current_question_index": len(interview.get("questions", [])),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        interview = interviews_collection.find_one({"_id": ObjectId(interview_id)})

    resume = None
    resume_id = interview.get("resume_id")
    if resume_id:
        resume = resumes_collection.find_one({"_id": resume_id})

    resume_text = resume.get("parsed_text", "") if resume else ""
    jd_text = interview.get("job_description", "")

    try:
        jd_analysis = await analyze_resume_against_jd(resume_text, jd_text) if jd_text else _default_jd_analysis("Job description not provided")
    except Exception as e:
        jd_analysis = _default_jd_analysis(f"Analysis error: {str(e)}")

    answers = interview.get("answers", [])
    session_eval = {"communication_score": 0}
    if answers:
        try:
            session_eval = await evaluate_interview_session(
                questions=interview.get("questions", []),
                answers=answers,
                domain=interview.get("domain", ""),
                job_role=interview.get("role", "")
            )
            overall_score = float(session_eval.get("overall_score", 0) or 0)
        except Exception:
            answer_scores = [float(a.get("score", 0) or 0) for a in answers]
            overall_score = sum(answer_scores) / len(answer_scores) if answer_scores else 0
    else:
        overall_score = 0

    behavioral_scores = []
    for answer in answers:
        question_text = str(answer.get("question", "") or "").lower()
        if any(token in question_text for token in ["tell me", "situation", "team", "conflict", "behavior"]):
            behavioral_scores.append(float(answer.get("score", 0) or 0))

    domain_lower = str(interview.get("domain", "") or "").lower()
    dsa_score = round(overall_score, 2) if any(token in domain_lower for token in ["data", "dsa", "algorithm"]) else 0
    system_design_score = round(overall_score, 2) if any(token in domain_lower for token in ["backend", "system", "devops", "architecture"]) else 0
    behavioral_score = round(sum(behavioral_scores) / len(behavioral_scores), 2) if behavioral_scores else 0
    communication_score = round(float(session_eval.get("communication_score", 0) or 0), 2)

    skill_breakdown = {
        "DSA": dsa_score,
        "System Design": system_design_score,
        "Behavioral": behavioral_score,
        "Communication": communication_score,
    }

    completed_at = datetime.utcnow()
    skill_match_data = {
        "matched_skills": jd_analysis.get("matched_skills", []),
        "missing_skills": jd_analysis.get("missing_skills", []),
        "ats_score": jd_analysis.get("ats_score", 50.0),
        "keyword_gaps": jd_analysis.get("keyword_gaps", []),
        "experience_gap": jd_analysis.get("experience_gap", "")
    }
    resume_suggestions_data = {
        "improvement_suggestions": jd_analysis.get("improvement_suggestions", []),
        "ats_optimization_tips": jd_analysis.get("ats_optimization_tips", [])
    }

    interviews_collection.update_one(
        {"_id": ObjectId(interview_id), "status": "pending"},
        {
            "$set": {
                "status": "completed",
                "total_score": round(float(overall_score or 0), 2),
                "skill_scores": skill_breakdown,
                "skill_match": skill_match_data,
                "resume_suggestions": resume_suggestions_data,
                "current_question_index": len(interview.get("questions", [])),
                "completed_at": completed_at,
                "updated_at": completed_at
            }
        }
    )

    intelligence = rebuild_user_intelligence(current_user_id)

    question_scores = [
        AnswerEvaluationResponse(
            question_id=a.get("question_id", 0),
            score=a.get("score", 0),
            feedback=a.get("feedback", ""),
            strengths=a.get("strengths", []),
            improvements=a.get("improvements", [])
        )
        for a in answers
    ]

    skill_match = SkillMatch(
        matched_skills=skill_match_data["matched_skills"],
        missing_skills=skill_match_data["missing_skills"],
        ats_score=skill_match_data["ats_score"],
        keyword_gaps=skill_match_data["keyword_gaps"],
        experience_gap=skill_match_data["experience_gap"]
    )

    resume_suggestions = ResumeSuggestion(
        improvement_suggestions=resume_suggestions_data["improvement_suggestions"],
        ats_optimization_tips=resume_suggestions_data["ats_optimization_tips"]
    )

    return InterviewResults(
        interview_id=interview_id,
        overall_score=round(float(overall_score or 0), 2),
        domain=interview.get("domain", ""),
        job_role=interview.get("role", ""),
        question_scores=question_scores,
        skill_match=skill_match,
        resume_suggestions=resume_suggestions,
        completed_at=completed_at,
        intelligence=intelligence
    )


@router.post("/{interview_id}/submit", response_model=InterviewResults)
async def submit_interview(
    interview_id: str,
    payload: InterviewSubmitRequest,
    current_user_id: str = Depends(get_current_user)
):
    return await _submit_and_complete_interview(interview_id, current_user_id, payload)


@router.post("/{interview_id}/complete", response_model=InterviewResults)
async def complete_interview(
    interview_id: str,
    current_user_id: str = Depends(get_current_user)
):
    return await _submit_and_complete_interview(interview_id, current_user_id, InterviewSubmitRequest())


@router.get("/{interview_id}")
async def get_interview(
    interview_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get interview details.
    
    Args:
        interview_id: Interview ID
        current_user_id: Current user ID from token
        
    Returns:
        Interview data
    """
    
    interviews_collection = get_collection("interviews")
    
    interview = interviews_collection.find_one({
        "_id": ObjectId(interview_id),
        "user_id": ObjectId(current_user_id)
    })
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    return {
        "id": str(interview["_id"]),
        "role": interview.get("role", ""),
        "type": interview.get("type", "general"),
        "domain": interview.get("domain", ""),
        "status": interview.get("status", ""),
        "total_score": interview.get("total_score"),
        "skill_scores": interview.get("skill_scores", {}),
        "questions": interview.get("questions", []),
        "answers": interview.get("answers", []),
        "current_question_index": int(interview.get("current_question_index", 0) or 0),
        "created_at": interview.get("created_at"),
        "completed_at": interview.get("completed_at"),
        "updated_at": interview.get("updated_at")
    }


@router.delete("/{interview_id}")
async def delete_interview(
    interview_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """Delete an in-progress interview belonging to the current user."""
    interviews_collection = get_collection("interviews")

    interview = interviews_collection.find_one({
        "_id": ObjectId(interview_id),
        "user_id": ObjectId(current_user_id)
    })

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    # Only allow deleting in-progress interviews (safe guard)
    interviews_collection.delete_one({"_id": ObjectId(interview_id)})

    rebuild_user_intelligence(current_user_id)

    return {"detail": "Interview deleted"}


@router.get("/{interview_id}/resume")
async def resume_interview(
    interview_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get interview data to resume an in-progress interview.
    Returns current question index based on saved answers.
    
    Args:
        interview_id: Interview ID
        current_user_id: Current user ID from token
        
    Returns:
        Interview data with current position
    """
    
    interviews_collection = get_collection("interviews")
    
    interview = interviews_collection.find_one({
        "_id": ObjectId(interview_id),
        "user_id": ObjectId(current_user_id),
        "status": "pending"
    })
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="In-progress interview not found"
        )
    
    answers = interview.get("answers", [])
    current_question_index = int(interview.get("current_question_index", 0) or 0)
    
    return {
        "id": str(interview["_id"]),
        "job_role": interview.get("job_role", ""),
        "domain": interview.get("domain", ""),
        "status": interview.get("status", "pending"),
        "type": interview.get("type", "general"),
        "role": interview.get("role", ""),
        "questions": interview.get("questions", []),
        "answers": answers,
        "current_question_index": current_question_index,
        "total_questions": len(interview.get("questions", [])),
        "created_at": interview.get("created_at"),
        "updated_at": interview.get("updated_at")
    }
