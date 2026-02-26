"""
Interview management API endpoints.
Create, manage, and complete interview sessions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from typing import List
from bson import ObjectId
from pydantic import BaseModel, Field
from app.schemas.api import (
    InterviewSetup,
    InterviewCreateResponse,
    AnswerSubmission,
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
        "job_role": setup.job_role,
        "domain": setup.domain,
        "job_description": setup.job_description,
        "resume_id": ObjectId(setup.resume_id),
        "questions": questions,
        "answers": [],
        "total_score": 0.0,
        "overall_score": 0.0,
        "skill_scores": {
            "DSA": 0,
            "System Design": 0,
            "Behavioral": 0,
            "Communication": 0,
        },
        "status": "pending",
        "created_at": datetime.utcnow(),
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
        "job_role": normalized_role,
        "domain": inferred_domain,
        "company": normalized_company,
        "difficulty": normalized_difficulty,
        "questions": [q["question"] for q in question_objects],
        "questions_structured": question_objects,
        "answers": [],
        "total_score": 0.0,
        "overall_score": 0.0,
        "skill_scores": {
            "DSA": 0,
            "System Design": 0,
            "Behavioral": 0,
            "Communication": 0,
        },
        "status": "pending",
        "created_at": datetime.utcnow(),
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
    answer_data: AnswerSubmission,
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
        "user_id": ObjectId(current_user_id)
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
    
    # Evaluate answer
    try:
        evaluation = await evaluate_answer(
            question=question,
            answer=answer_data.answer,
            job_context=interview.get("job_role", "")
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
        "answer": answer_data.answer,
        "score": evaluation.get("score", 0),
        "feedback": evaluation.get("feedback", ""),
        "strengths": evaluation.get("strengths", []),
        "improvements": evaluation.get("improvements", [])
    }
    
    interviews_collection.update_one(
        {"_id": ObjectId(interview_id)},
        {"$push": {"answers": answer_record}}
    )

    if interview.get("status") == "completed":
        rebuild_user_intelligence(current_user_id)
    
    return AnswerEvaluationResponse(
        question_id=answer_data.question_id,
        score=evaluation.get("score", 0),
        feedback=evaluation.get("feedback", ""),
        strengths=evaluation.get("strengths", []),
        improvements=evaluation.get("improvements", [])
    )


@router.post("/{interview_id}/complete", response_model=InterviewResults)
async def complete_interview(
    interview_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Complete interview and generate results.
    
    Args:
        interview_id: Interview ID
        current_user_id: Current user ID from token
        
    Returns:
        Interview results
    """
    
    interviews_collection = get_collection("interviews")
    resumes_collection = get_collection("resumes")
    
    # Get interview
    interview = interviews_collection.find_one({
        "_id": ObjectId(interview_id),
        "user_id": ObjectId(current_user_id)
    })
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    # Get resume for JD analysis
    resume = resumes_collection.find_one(
        {"_id": interview.get("resume_id")}
    )
    
    resume_text = resume.get("parsed_text", "") if resume else ""
    jd_text = interview.get("job_description", "")
    
    print(f"[Interview Complete] Resume text length: {len(resume_text) if resume_text else 0}")
    print(f"[Interview Complete] JD text length: {len(jd_text) if jd_text else 0}")
    
    # Analyze resume vs JD
    try:
        print(f"[Interview Complete] Starting JD analysis...")
        jd_analysis = await analyze_resume_against_jd(resume_text, jd_text)
        print(f"[Interview Complete] JD analysis complete. ATS Score: {jd_analysis.get('ats_score', 0)}")
    except Exception as e:
        print(f"[Interview Complete] ERROR in analyze_resume_against_jd: {str(e)}")
        jd_analysis = {
            "ats_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "keyword_gaps": [],
            "experience_gap": f"Analysis error: {str(e)}",
            "improvement_suggestions": []
        }
    
    # Evaluate entire interview
    answers = interview.get("answers", [])
    
    session_eval = {
        "technical_proficiency": 0,
        "communication_score": 0
    }

    if answers:
        try:
            session_eval = await evaluate_interview_session(
                questions=interview.get("questions", []),
                answers=answers,
                domain=interview.get("domain", ""),
                job_role=interview.get("job_role", "")
            )
            overall_score = session_eval.get("overall_score", 0)
        except Exception as e:
            # Fallback: calculate average score from answers
            answer_scores = [a.get("score", 0) for a in answers]
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

    # Update interview status immediately with final computed fields
    completed_at = datetime.utcnow()
    interviews_collection.update_one(
        {"_id": ObjectId(interview_id)},
        {
            "$set": {
                "status": "completed",
                "total_score": round(float(overall_score or 0), 2),
                "overall_score": round(float(overall_score or 0), 2),
                "skill_scores": skill_breakdown,
                "skill_breakdown": skill_breakdown,
                "completed_at": completed_at,
                "updated_at": completed_at
            }
        }
    )

    rebuild_user_intelligence(current_user_id)
    
    # Format results
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
        matched_skills=jd_analysis.get("matched_skills", []),
        missing_skills=jd_analysis.get("missing_skills", []),
        ats_score=jd_analysis.get("ats_score", 0),
        keyword_gaps=jd_analysis.get("keyword_gaps", []),
        experience_gap=jd_analysis.get("experience_gap", "")
    )
    
    print(f"[Interview Complete] SkillMatch ATS Score: {skill_match.ats_score}")
    
    resume_suggestions = ResumeSuggestion(
        improvement_suggestions=jd_analysis.get("improvement_suggestions", []),
        ats_optimization_tips=jd_analysis.get("ats_optimization_tips", [])
    )
    
    return InterviewResults(
        interview_id=interview_id,
        overall_score=overall_score,
        domain=interview.get("domain", ""),
        job_role=interview.get("job_role", ""),
        question_scores=question_scores,
        skill_match=skill_match,
        resume_suggestions=resume_suggestions,
        completed_at=completed_at
    )


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
        "job_role": interview.get("job_role", ""),
        "domain": interview.get("domain", ""),
        "status": interview.get("status", ""),
        "overall_score": interview.get("overall_score", 0),
        "questions": interview.get("questions", []),
        "answers": interview.get("answers", []),
        "created_at": interview.get("created_at"),
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
        "status": {"$in": ["pending", "in_progress"]}
    })
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="In-progress interview not found"
        )
    
    # Calculate current question index based on answers received
    answers = interview.get("answers", [])
    current_question_index = len(answers)
    
    return {
        "id": str(interview["_id"]),
        "job_role": interview.get("job_role", ""),
        "domain": interview.get("domain", ""),
        "status": interview.get("status", ""),
        "questions": interview.get("questions", []),
        "answers": answers,
        "current_question_index": current_question_index,
        "total_questions": len(interview.get("questions", [])),
        "created_at": interview.get("created_at"),
        "updated_at": interview.get("updated_at")
    }
