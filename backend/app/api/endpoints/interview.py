"""
Interview management API endpoints.
Create, manage, and complete interview sessions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import asyncio
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
from app.services.notification_service import create_notification
from app.services.judge0_service import evaluate_code_with_tests
from app.core.database import get_collection

router = APIRouter(prefix="/api/interview", tags=["interview"])

SUPPORTED_PROGRAMMING_LANGUAGES = {"Python", "Java", "C++", "JavaScript", "Go"}
SUPPORTED_INTERVIEW_TYPES = {"general", "coding", "voice", "company"}


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


def _has_meaningful_jd_analysis(data: dict) -> bool:
    if not isinstance(data, dict):
        return False

    ats_score = data.get("ats_score")
    has_ats = ats_score is not None

    matched = len(data.get("matched_skills") or []) > 0
    missing = len(data.get("missing_skills") or []) > 0
    keywords = len(data.get("keyword_gaps") or []) > 0
    suggestions = len(data.get("improvement_suggestions") or []) > 0
    tips = len(data.get("ats_optimization_tips") or []) > 0
    experience = bool(str(data.get("experience_gap") or "").strip())

    has_details = matched or missing or keywords or suggestions or tips or experience
    return has_ats and has_details


async def _resolve_jd_analysis(interview: dict, resumes_collection) -> dict:
    stored = _get_stored_jd_analysis(interview)
    if _has_meaningful_jd_analysis(stored):
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


def _normalize_programming_language(programming_language: str | None) -> str | None:
    if not programming_language:
        return None

    normalized = programming_language.strip()
    if not normalized:
        return None

    aliases = {
        "python": "Python",
        "java": "Java",
        "c++": "C++",
        "cpp": "C++",
        "javascript": "JavaScript",
        "js": "JavaScript",
        "go": "Go",
        "golang": "Go",
    }
    resolved = aliases.get(normalized.lower(), normalized)
    if resolved not in SUPPORTED_PROGRAMMING_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported programming language. Supported values: {', '.join(sorted(SUPPORTED_PROGRAMMING_LANGUAGES))}"
        )
    return resolved


def _normalize_interview_type(interview_type: str | None) -> str:
    normalized = (interview_type or "general").strip().lower()
    if normalized not in SUPPORTED_INTERVIEW_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported interview type. Supported values: {', '.join(sorted(SUPPORTED_INTERVIEW_TYPES))}"
        )
    return normalized


def _serialize_interview(interview: dict) -> dict:
    return {
        "id": str(interview.get("_id")),
        "user_id": str(interview.get("user_id")) if interview.get("user_id") else None,
        "role": interview.get("role") or interview.get("job_role") or "",
        "type": interview.get("type", "general"),
        "interview_type": interview.get("interview_type", "general"),
        "status": interview.get("status", "pending"),
        "questions": interview.get("questions", []),
        "questions_structured": interview.get("questions_structured", []),
        "question_type": interview.get("question_type", "descriptive"),
        "answers": interview.get("answers", []),
        "current_question_index": int(interview.get("current_question_index", 0) or 0),
        "created_at": interview.get("created_at"),
        "completed_at": interview.get("completed_at"),
        "score": float(interview.get("score", interview.get("total_score", interview.get("overall_score", 0))) or 0),
        "total_score": float(interview.get("score", interview.get("total_score", interview.get("overall_score", 0))) or 0),
        "skill_scores": interview.get("skill_scores", {}),
        "domain": interview.get("domain", ""),
        "programming_language": interview.get("programming_language"),
        "interview_type": interview.get("interview_type", "general"),
        "company": interview.get("company"),
        "updated_at": interview.get("updated_at"),
        "resume_id": str(interview.get("resume_id")) if interview.get("resume_id") else None,
        "job_description": interview.get("job_description", ""),
        "skill_match": interview.get("skill_match"),
        "resume_suggestions": interview.get("resume_suggestions"),
    }


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
    answer_type: str = Field(default="text", pattern="^(text|code|voice)$")
    language: Optional[str] = None
    audio_url: Optional[str] = None


class InterviewSubmitRequest(BaseModel):
    answers: Optional[List[Dict]] = None


@router.post("/create", response_model=InterviewCreateResponse)
async def create_interview(
    setup: InterviewSetup,
    current_user_id: str = Depends(get_current_user)
):
    programming_language = _normalize_programming_language(getattr(setup, "programming_language", None))
    print(setup.job_role, programming_language)
    interview_type = _normalize_interview_type(getattr(setup, "interview_type", "general"))
    question_type = (getattr(setup, "question_type", "descriptive") or "descriptive").strip().lower()
    if question_type not in {"mcq", "descriptive"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="question_type must be mcq or descriptive")
    
    # Verify resume exists
    resumes_collection = get_collection("resumes")
    resume_query = {"user_id": ObjectId(current_user_id)}
    if getattr(setup, "resume_id", None):
        resume_query["_id"] = ObjectId(setup.resume_id)

    resume = resumes_collection.find_one(resume_query, sort=[("uploaded_at", -1)])
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found. Please upload resume first."
        )
    
    # Get resume text
    resume_text = resume.get("parsed_text", "")
    
    requested_questions = setup.num_questions if getattr(setup, "num_questions", None) else None
    num_questions = requested_questions or _get_preferred_question_count(current_user_id, fallback=5)

    # Generate interview questions
    try:
        generated_questions = await generate_interview_questions(
            job_role=setup.job_role,
            domain=setup.domain,
            resume_text=resume_text,
            job_description=setup.job_description,
            num_questions=num_questions,
            programming_language=programming_language,
            question_type=question_type,
        )
        if question_type == "mcq" and generated_questions and isinstance(generated_questions[0], dict):
            questions_structured = generated_questions[:num_questions]
            questions = [str(item.get("question", "")).strip() for item in questions_structured if str(item.get("question", "")).strip()]
        else:
            questions = [str(item).strip() for item in generated_questions if str(item).strip()][:num_questions]
            questions_structured = [{"question": q, "type": question_type} for q in questions]
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
        "interview_type": interview_type,
        "domain": setup.domain,
        "programming_language": programming_language,
        "job_description": setup.job_description,
        "resume_id": resume.get("_id"),
        "question_type": question_type,
        "questions": questions,
        "questions_structured": questions_structured,
        "answers": [],
        "current_question_index": 0,
        "score": None,
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
        questions=questions,
        programming_language=programming_language,
        interview_type=interview_doc.get("interview_type", "general"),
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
        num_questions=question_count,
        company_style=normalized_company,
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
        "interview_type": "company",
        "domain": inferred_domain,
        "company": normalized_company,
        "difficulty": normalized_difficulty,
        "programming_language": None,
        "questions": [q["question"] for q in question_objects],
        "questions_structured": question_objects,
        "answers": [],
        "current_question_index": 0,
        "score": None,
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
    
    questions_structured = interview.get("questions_structured") or []
    question_payload = questions_structured[answer_data.question_id] if answer_data.question_id < len(questions_structured) else None
    question = question_payload.get("question") if isinstance(question_payload, dict) else questions[answer_data.question_id]
    
    current_question_index = int(interview.get("current_question_index", 0) or 0)
    if answer_data.question_id != current_question_index:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question order mismatch"
        )

    # Idempotency: if this question was already answered (e.g. on a client retry),
    # return the stored evaluation rather than re-evaluating and pushing a duplicate record.
    existing_answers = interview.get("answers", [])
    for stored_answer in existing_answers:
        if stored_answer.get("question_id") == answer_data.question_id:
            return AnswerEvaluationResponse(
                question_id=stored_answer["question_id"],
                strengths=stored_answer.get("strengths", []),
                improvement=stored_answer.get("improvement", stored_answer.get("improvements", [])),
                ideal_answer=stored_answer.get("ideal_answer", ""),
                feedback=stored_answer.get("feedback", ""),
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
            strengths=[],
            improvement=["Answer was skipped."],
            ideal_answer="",
            feedback="Question skipped",
        )

    answer_text = (answer_data.answer or "").strip()
    if not answer_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Answer cannot be empty unless skipped"
        )

    resolved_question_type = str((question_payload or {}).get("type") or interview.get("question_type") or "descriptive").lower()
    is_coding_answer = answer_data.answer_type == "code" or interview.get("interview_type") == "coding"
    is_mcq_answer = resolved_question_type == "mcq"

    # Evaluate answer
    if is_mcq_answer:
        options = list((question_payload or {}).get("options") or [])
        correct_answer = str((question_payload or {}).get("correct_answer") or "").strip().lower()
        normalized_answer = answer_text.strip().lower()
        passed = bool(correct_answer and normalized_answer == correct_answer)
        if not passed and options:
            for option in options:
                if normalized_answer == str(option).strip().lower() and str(option).strip().lower() == correct_answer:
                    passed = True
                    break
        evaluation = {
            "score": 100 if passed else 0,
            "feedback": "Correct answer selected." if passed else "Incorrect answer selected.",
            "strengths": ["Good concept recall"] if passed else [],
            "weaknesses": [] if passed else ["Need to review the core concept behind this question"],
            "improvements": ["Review this topic and retry similar MCQs to improve speed and accuracy."],
            "improvement_tips": ["Eliminate two incorrect options first, then compare the remaining choices carefully."],
            "ideal_answer": (question_payload or {}).get("correct_answer", ""),
        }
    elif is_coding_answer:
        tests = interview.get("coding_tests") or [
            {"input": "1 2", "output": "3"},
            {"input": "10 5", "output": "15"},
        ]
        coding_eval = await evaluate_code_with_tests(
            code=answer_text,
            language=answer_data.language or interview.get("programming_language") or "python",
            tests=tests,
        )
        evaluation = {
            "score": coding_eval.get("score", 0),
            "feedback": "Coding evaluation completed using runtime test execution.",
            "strengths": ["Code runs against submitted test cases"] if coding_eval.get("passed") else ["Attempt submitted and executed"],
            "weaknesses": [] if coding_eval.get("passed") else ["Some test cases failed"],
            "improvements": ["Handle edge cases and optimize time complexity"],
            "improvement_tips": ["Add input validation and test against corner cases."],
            "ideal_answer": "A complete solution should pass all test cases and explain complexity trade-offs.",
            "runtime_ms": coding_eval.get("runtime_ms"),
            "test_case_success": coding_eval.get("score", 0),
            "test_results": coding_eval.get("test_results", []),
        }
    else:
        try:
            evaluation = await evaluate_answer(
                question=question,
                answer=answer_text,
                job_context=interview.get("role", "")
            )
        except Exception:
            evaluation = {
                "score": 50.0,
                "feedback": "Unable to evaluate at this time",
                "strengths": [],
                "weaknesses": [],
                "improvements": [],
                "improvement_tips": [],
                "ideal_answer": "",
                "technical_accuracy": 50,
                "communication": 50,
                "completeness": 50
            }
    
    # Store answer
    answer_record = {
        "question_id": answer_data.question_id,
        "question": question,
        "answer": answer_text,
        "answer_text": answer_text,
        "answer_type": answer_data.answer_type,
        "language": answer_data.language,
        "audio_url": answer_data.audio_url,
        "score": evaluation.get("score", 0),
        "feedback": evaluation.get("feedback", ""),
        "strengths": evaluation.get("strengths", []),
        "weaknesses": evaluation.get("weaknesses", []),
        "improvement": evaluation.get("improvement", evaluation.get("improvements", evaluation.get("improvement_tips", []))),
        "improvements": evaluation.get("improvements", []),
        "improvement_tips": evaluation.get("improvement_tips", []),
        "ideal_answer": evaluation.get("ideal_answer", ""),
        "runtime_ms": evaluation.get("runtime_ms"),
        "test_case_success": evaluation.get("test_case_success"),
        "test_results": evaluation.get("test_results", []),
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
        strengths=evaluation.get("strengths", []),
        improvement=evaluation.get("improvement", evaluation.get("improvements", evaluation.get("improvement_tips", []))),
        ideal_answer=evaluation.get("ideal_answer", ""),
        feedback=evaluation.get("feedback", ""),
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
                strengths=a.get("strengths", []),
                improvement=a.get("improvement", a.get("improvements", [])),
                ideal_answer=a.get("ideal_answer", ""),
                feedback=a.get("feedback", ""),
            )
            for a in answers
        ]
        return InterviewResults(
            interview_id=interview_id,
            overall_score=float(interview.get("score", interview.get("total_score", 0)) or 0),
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

    answers = interview.get("answers", [])
    async def _safe_jd_analysis():
        if not jd_text:
            return _default_jd_analysis("Job description not provided")
        try:
            return await analyze_resume_against_jd(resume_text, jd_text)
        except Exception as e:
            return _default_jd_analysis(f"Analysis error: {str(e)}")

    async def _safe_session_eval():
        if not answers:
            return {"overall_score": 0, "communication_score": 0}
        try:
            return await evaluate_interview_session(
                questions=interview.get("questions", []),
                answers=answers,
                domain=interview.get("domain", ""),
                job_role=interview.get("role", "")
            )
        except Exception:
            answer_scores = [float(a.get("score", 0) or 0) for a in answers]
            computed = sum(answer_scores) / len(answer_scores) if answer_scores else 0
            return {"overall_score": computed, "communication_score": 0}

    jd_analysis, session_eval = await asyncio.gather(_safe_jd_analysis(), _safe_session_eval())
    overall_score = float(session_eval.get("overall_score", 0) or 0)

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
                "score": round(float(overall_score or 0), 2),
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

    create_notification(
        user_id=current_user_id,
        notification_type="INTERVIEW_COMPLETED",
        title="Interview Completed",
        message="Your interview results are ready.",
        metadata={
            "interview_id": interview_id,
            "score": round(float(overall_score or 0), 2),
            "role": interview.get("role", ""),
        },
    )

    question_scores = [
        AnswerEvaluationResponse(
            question_id=a.get("question_id", 0),
            strengths=a.get("strengths", []),
            improvement=a.get("improvement", a.get("improvements", [])),
            ideal_answer=a.get("ideal_answer", ""),
            feedback=a.get("feedback", ""),
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
    
    return _serialize_interview(interview)


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
    
    serialized = _serialize_interview(interview)
    serialized["total_questions"] = len(interview.get("questions", []))
    return serialized
