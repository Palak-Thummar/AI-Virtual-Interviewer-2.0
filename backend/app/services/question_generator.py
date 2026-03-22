"""
Interview question generator service.
Generates personalized interview questions based on role, domain, resume, and JD.
"""

import json
import re
from typing import Any, List
from openai import OpenAI
from app.core.config import settings, get_available_models_formatted


# Configure OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY
)

_QUESTION_CACHE: dict[str, List[Any]] = {}
_QUESTION_CACHE_MAX = 128

LANGUAGE_MARKERS = {
    "python": ["python", "pip", "pandas", "django", "flask"],
    "java": ["java", "jvm", "spring", "maven", "gradle"],
    "javascript": ["javascript", "node", "npm", "react", "express"],
    "go": ["go", "golang", "goroutine", "go module"],
    "c++": ["c++", "cpp", "stl", "template", "pointer"],
}


async def generate_interview_questions(
    job_role: str,
    domain: str,
    resume_text: str,
    job_description: str,
    num_questions: int = 5,
    programming_language: str | None = None,
    company_style: str | None = None,
    question_type: str = "descriptive",
) -> List[Any]:
    """
    Generate personalized interview questions.
    
    Uses OpenRouter AI to create questions tailored to:
    - Job role and domain
    - Candidate's resume background
    - Specific job requirements in JD
    
    Args:
        job_role: Job role/position title
        domain: Technical domain (e.g., Backend, Frontend, DevOps)
        resume_text: Candidate's resume text
        job_description: Job description text
        num_questions: Number of questions to generate
        
    Returns:
        List of interview questions
    """
    
    programming_context = programming_language.strip() if programming_language else ""
    language_line = f"PROGRAMMING LANGUAGE: {programming_context}\n" if programming_context else ""
    company_line = f"COMPANY STYLE: {company_style}\n" if company_style else ""

    normalized_question_type = (question_type or "descriptive").strip().lower()
    is_mcq = normalized_question_type == "mcq"

    cache_key = "|".join(
        [
            job_role.strip().lower(),
            domain.strip().lower(),
            normalized_question_type,
            str(num_questions),
            (programming_context or "").lower(),
            (company_style or "").strip().lower(),
            resume_text[:400].strip().lower(),
            job_description[:400].strip().lower(),
        ]
    )
    if cache_key in _QUESTION_CACHE:
        return _QUESTION_CACHE[cache_key][:num_questions]

    format_requirements = (
        f"Return ONLY valid JSON array of exactly {num_questions} objects in this shape: "
        "[{\"question\":\"...\",\"options\":[\"A\",\"B\",\"C\",\"D\"],\"correct_answer\":\"A\",\"type\":\"mcq\"}]"
        if is_mcq
        else f"Return ONLY valid JSON array of exactly {num_questions} question strings."
    )

    prompt = f"""You are a senior technical interviewer with 20+ years of experience.

Generate {num_questions} personalized technical interview questions based on:

JOB ROLE: {job_role}
DOMAIN: {domain}
{company_line}{language_line}CANDIDATE RESUME:
{resume_text[:900]}

JOB DESCRIPTION:
{job_description[:900]}

Requirements:
- Questions should be personalized to the candidate's experience level
- Mix behavioral, technical, and situational questions
- Questions should align with the specific job requirements
- If a programming language is provided, every technical question must be strictly about that language only
- Do not reference or compare with other programming languages when a language is provided
- Make them challenging but fair
- QUESTION TYPE MODE: {normalized_question_type}
- {format_requirements}

Generate exactly {num_questions} questions. Return only the JSON array, no markdown."""

    retry_prompt = (
        prompt
        + "\n\nIMPORTANT RETRY CONSTRAINTS:\n"
        + "- Re-generate and ensure every question is strictly tied to the requested programming language.\n"
        + "- Reject any mention of other programming languages."
    )

    try:
        for attempt in range(2):
            response = await _call_openrouter(prompt if attempt == 0 else retry_prompt)
            questions = _parse_json_response(response)

            if not isinstance(questions, list):
                continue

            if is_mcq and questions and isinstance(questions[0], dict):
                normalized = []
                for item in questions:
                    question_text = str(item.get("question", "")).strip()
                    options = [str(opt).strip() for opt in (item.get("options") or []) if str(opt).strip()]
                    correct_answer = str(item.get("correct_answer", "")).strip()
                    if question_text and len(options) >= 2:
                        normalized.append(
                            {
                                "question": question_text,
                                "options": options[:4],
                                "correct_answer": correct_answer or options[0],
                                "type": "mcq",
                            }
                        )

                if normalized and _questions_match_requested_language(normalized, programming_context):
                    _QUESTION_CACHE[cache_key] = normalized[:num_questions]
                    if len(_QUESTION_CACHE) > _QUESTION_CACHE_MAX:
                        _QUESTION_CACHE.pop(next(iter(_QUESTION_CACHE)))
                    return normalized[:num_questions]
                continue

            normalized_strings = [q.strip() for q in questions if isinstance(q, str)]
            if normalized_strings and _questions_match_requested_language(normalized_strings, programming_context):
                _QUESTION_CACHE[cache_key] = normalized_strings[:num_questions]
                if len(_QUESTION_CACHE) > _QUESTION_CACHE_MAX:
                    _QUESTION_CACHE.pop(next(iter(_QUESTION_CACHE)))
                return normalized_strings[:num_questions]

        return _generate_fallback_questions(job_role, domain, num_questions, programming_context, normalized_question_type)

    except Exception:
        return _generate_fallback_questions(job_role, domain, num_questions, programming_context, normalized_question_type)


async def generate_follow_up_question(
    original_question: str,
    answer: str,
    domain: str
) -> str:
    """
    Generate a follow-up question based on candidate's answer.
    
    Args:
        original_question: Original question asked
        answer: Candidate's answer
        domain: Technical domain
        
    Returns:
        Follow-up question
    """
    
    prompt = f"""You are a technical interviewer. Based on this Q&A, generate ONE thoughtful follow-up question.

QUESTION: {original_question}
ANSWER: {answer[:500]}
DOMAIN: {domain}

Return ONLY the follow-up question as a string, no JSON formatting, no numbering."""

    try:
        response = await _call_openrouter(prompt)
        return response.strip()
    except Exception as e:
        return f"Can you elaborate more on your approach to this {domain} challenge?"


# ============= HELPER FUNCTIONS =============

async def _call_openrouter(prompt: str) -> str:
    """Call OpenRouter API with prompt."""
    try:
        if not settings.OPENROUTER_API_KEY:
            raise Exception("OPENROUTER_API_KEY not configured")
        
        response = client.chat.completions.create(
            model=settings.OPENROUTER_MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"[QuestionGenerator] OpenRouter API error: {e}")
        available = get_available_models_formatted()
        print(f"[QuestionGenerator] Models available: {available}")
        raise Exception(f"OpenRouter API error: {str(e)}. Available models: {available}")


def _parse_json_response(response: str) -> list:
    """Parse JSON array from AI response."""
    try:
        # Extract JSON array from response
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON response: {response[:100]}")


def _questions_match_requested_language(questions: List[Any], programming_language: str | None) -> bool:
    if not programming_language:
        return True

    selected = programming_language.strip().lower()
    markers = LANGUAGE_MARKERS.get(selected)
    if not markers:
        return True

    all_text = []
    for item in questions:
        if isinstance(item, dict):
            all_text.append(str(item.get("question", "")))
            all_text.extend([str(opt) for opt in (item.get("options") or [])])
        else:
            all_text.append(str(item))

    blob = "\n".join(all_text).lower()
    has_selected = any(marker in blob for marker in markers)
    if not has_selected:
        return False

    for language, language_markers in LANGUAGE_MARKERS.items():
        if language == selected:
            continue
        if any(marker in blob for marker in language_markers):
            return False

    return True


def _generate_fallback_questions(role: str, domain: str, count: int, programming_language: str | None = None, question_type: str = "descriptive") -> List[Any]:
    """
    Generate fallback questions if AI generation fails.
    Provides sensible default questions.
    """
    
    language_phrase = f" using {programming_language}" if programming_language else ""

    all_questions = [
        f"Walk us through your most challenging {domain} project and how you solved it.",
        f"What experience do you have with the tech stack and core tools required for a {role}{language_phrase} role?",
        f"Describe your approach to designing a scalable {domain} solution{language_phrase}.",
        f"Tell us about a time you had to learn a new technology quickly in {domain}.",
        f"How do you stay updated with the latest trends and best practices in {domain}?",
        f"What testing and debugging strategies do you use in your {domain} work{language_phrase}?",
        f"Describe your experience working in a team environment for {domain} projects.",
        f"What would you do if you faced a critical production issue in {domain}?",
        f"How do you approach code review and receiving feedback on your {domain} code{language_phrase}?",
        f"What are your long-term career goals in {domain}?",
    ]
    
    if question_type == "mcq":
        mcq = []
        for text in all_questions[:count]:
            mcq.append(
                {
                    "question": text,
                    "options": [
                        "Approach A",
                        "Approach B",
                        "Approach C",
                        "Approach D",
                    ],
                    "correct_answer": "Approach A",
                    "type": "mcq",
                }
            )
        return mcq

    return all_questions[:count]
