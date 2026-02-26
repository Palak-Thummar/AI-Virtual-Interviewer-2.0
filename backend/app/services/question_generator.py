"""
Interview question generator service.
Generates personalized interview questions based on role, domain, resume, and JD.
"""

import json
import re
from typing import List
from openai import OpenAI
from app.core.config import settings, get_available_models_formatted


# Configure OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY
)


async def generate_interview_questions(
    job_role: str,
    domain: str,
    resume_text: str,
    job_description: str,
    num_questions: int = 5
) -> List[str]:
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
    
    prompt = f"""You are a senior technical interviewer with 20+ years of experience.

Generate {num_questions} personalized technical interview questions based on:

JOB ROLE: {job_role}
DOMAIN: {domain}
CANDIDATE RESUME:
{resume_text[:1500]}

JOB DESCRIPTION:
{job_description[:1500]}

Requirements:
- Questions should be personalized to the candidate's experience level
- Mix behavioral, technical, and situational questions
- Questions should align with the specific job requirements
- Make them challenging but fair
- Return a JSON array of questions only

Format (return ONLY valid JSON array):
["Question 1?", "Question 2?", ...]

Generate exactly {num_questions} questions. Return only the JSON array, no markdown."""

    try:
        response = await _call_openrouter(prompt)
        questions = _parse_json_response(response)
        
        if isinstance(questions, list):
            questions = [q.strip() for q in questions if isinstance(q, str)]
            return questions[:num_questions]
        
        return _generate_fallback_questions(job_role, domain, num_questions)
        
    except Exception as e:
        print(f"Error generating questions: {e}")
        return _generate_fallback_questions(job_role, domain, num_questions)


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


def _generate_fallback_questions(role: str, domain: str, count: int) -> List[str]:
    """
    Generate fallback questions if AI generation fails.
    Provides sensible default questions.
    """
    
    all_questions = [
        f"Walk us through your most challenging {domain} project and how you solved it.",
        f"What experience do you have with the tech stack mentioned in the job description?",
        f"Describe your approach to designing a scalable {domain} solution.",
        f"Tell us about a time you had to learn a new technology quickly in {domain}.",
        f"How do you stay updated with the latest trends and best practices in {domain}?",
        f"What testing and debugging strategies do you use in your {domain} work?",
        f"Describe your experience working in a team environment for {domain} projects.",
        f"What would you do if you faced a critical production issue in {domain}?",
        f"How do you approach code review and receiving feedback on your {domain} code?",
        f"What are your long-term career goals in {domain}?",
    ]
    
    return all_questions[:count]
