"""
Interview evaluation engine service.
Evaluates candidate answers and provides detailed feedback and scoring.
"""

import json
import re
from typing import Dict
from openai import OpenAI
from app.core.config import settings, get_available_models_formatted


# Configure OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY
)


async def evaluate_answer(
    question: str,
    answer: str,
    job_context: str = ""
) -> Dict:
    """
    Evaluate a candidate's answer to an interview question.
    
    Evaluates on:
    - Relevance and completeness
    - Technical accuracy
    - Communication clarity
    - Problem-solving approach
    
    Args:
        question: Interview question
        answer: Candidate's answer
        job_context: Optional context about the job/domain
        
    Returns:
        Evaluation with score, feedback, strengths, and improvements
    """
    
    # Check if API key is configured
    if not settings.OPENROUTER_API_KEY:
        print("[ERROR] OPENROUTER_API_KEY not configured!")
        return _get_default_evaluation()
    
    prompt = f"""You are an expert technical interviewer. Evaluate this answer and provide a detailed score between 0 and 100.

QUESTION: {question}

CANDIDATE ANSWER: {answer}

JOB CONTEXT: {job_context}

Evaluate this answer fairly. For even short answers or single words, provide a realistic score (not necessarily high).

Return ONLY this JSON format (no markdown, no extra text, just raw JSON):
{{"score": 45, "feedback": "example", "strengths": ["example"], "improvements": ["example"], "technical_accuracy": 45, "communication": 45, "completeness": 45, "reasoning": "example"}}

CRITICAL: Your response must start with {{ and end with }} with no other text before or after."""

    try:
        print(f"[Evaluator] Starting evaluation...")
        print(f"[Evaluator] Question: {question[:60]}...")
        print(f"[Evaluator] Answer: {answer[:60]}...")
        print(f"[Evaluator] API Key configured: {bool(settings.OPENROUTER_API_KEY)}")
        
        response = await _call_openrouter(prompt)
        print(f"[Evaluator] OpenRouter response received: {response[:200]}...")
        
        evaluation = _parse_json_response(response)
        print(f"[Evaluator] Parsed JSON: {evaluation}")
        
        # Validate response
        evaluation = _validate_evaluation_response(evaluation)
        print(f"[Evaluator] Final score: {evaluation.get('score')}")
        return evaluation
        
    except Exception as e:
        print(f"[ERROR] Exception in evaluate_answer: {str(e)}")
        import traceback
        traceback.print_exc()
        return _get_default_evaluation()


async def evaluate_interview_session(
    questions: list,
    answers: list,
    domain: str,
    job_role: str
) -> Dict:
    """
    Evaluate entire interview session and calculate overall score.
    
    Args:
        questions: List of questions asked
        answers: List of evaluations for each answer
        domain: Technical domain
        job_role: Job role being interviewed for
        
    Returns:
        Overall interview evaluation
    """
    
    if not answers:
        return {"overall_score": 0.0, "recommendation": "No answers evaluated"}
    
    # Calculate overall score (weighted average)
    scores = [a.get("score", 0) for a in answers]
    overall_score = sum(scores) / len(scores) if scores else 0
    
    # Generate recommendation
    if overall_score >= 80:
        recommendation = "Strong candidate - Recommend for next round"
    elif overall_score >= 65:
        recommendation = "Qualified candidate - Good fit with some improvements"
    elif overall_score >= 50:
        recommendation = "Adequate candidate - May need additional screening"
    else:
        recommendation = "Needs improvement - Consider feedback areas"
    
    # Calculate domain proficiency
    tech_scores = [a.get("technical_accuracy", 0) for a in answers]
    tech_avg = sum(tech_scores) / len(tech_scores) if tech_scores else 0
    
    # Communication average
    comm_scores = [a.get("communication", 0) for a in answers]
    comm_avg = sum(comm_scores) / len(comm_scores) if comm_scores else 0
    
    return {
        "overall_score": round(overall_score, 2),
        "technical_proficiency": round(tech_avg, 2),
        "communication_score": round(comm_avg, 2),
        "recommendation": recommendation,
        "domain": domain,
        "job_role": job_role
    }


async def generate_interview_feedback(
    interview_summary: Dict,
    domain: str
) -> str:
    """
    Generate personalized feedback based on interview performance.
    
    Args:
        interview_summary: Summary of interview evaluations
        domain: Technical domain
        
    Returns:
        Personalized feedback text
    """
    
    prompt = f"""Generate personalized, constructive feedback for a candidate based on their interview performance.

INTERVIEW SUMMARY:
- Overall Score: {interview_summary.get('overall_score', 0)}/100
- Domain: {domain}
- Technical Proficiency: {interview_summary.get('technical_proficiency', 0)}/100
- Communication: {interview_summary.get('communication_score', 0)}/100
- Recommendation: {interview_summary.get('recommendation', '')}

Provide:
1. 2-3 sentences on overall performance
2. Key strengths demonstrated
3. Areas for improvement
4. Specific recommendations for growth
5. Next steps

Write in a professional but encouraging tone. 3-4 paragraphs total."""

    try:
        response = await _call_openrouter(prompt)
        return response.strip()
    except Exception as e:
        return "Interview feedback generation in progress. Please try again."


# ============= HELPER FUNCTIONS =============

async def _call_openrouter(prompt: str) -> str:
    """Call OpenRouter API with prompt."""
    try:
        print(f"[OpenRouter API] Calling OpenRouter with prompt length: {len(prompt)}")
        
        if not settings.OPENROUTER_API_KEY:
            raise Exception("OPENROUTER_API_KEY not configured")

        response = client.chat.completions.create(
            model=settings.OPENROUTER_MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        result = response.choices[0].message.content
        print(f"[OpenRouter API] Success! Response length: {len(result)}")
        print(f"[OpenRouter API] Response preview: {result[:150]}")
        return result
    except Exception as e:
        print(f"[OpenRouter API] ERROR: {str(e)}")
        print(f"[OpenRouter API] Error type: {type(e).__name__}")
        available = get_available_models_formatted()
        print(f"[OpenRouter API] Models available: {available}")
        raise Exception(f"OpenRouter API error: {str(e)}. Available models: {available}")


def _parse_json_response(response: str) -> dict:
    """Parse JSON from AI response - aggressive extraction."""
    
    print(f"[Parser] Raw response: {response[:300]}...")
    
    try:
        # Clean up the response
        cleaned = response.strip()
        print(f"[Parser] After strip: {cleaned[:200]}...")
        
        # Remove markdown code blocks if present
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
            if cleaned.startswith('json'):
                cleaned = cleaned[4:]
            if cleaned.startswith('\n'):
                cleaned = cleaned[1:]
            cleaned = cleaned.rstrip('`')
        
        cleaned = cleaned.strip()
        print(f"[Parser] After markdown removal: {cleaned[:200]}...")
        
        # Try direct parse first
        try:
            parsed = json.loads(cleaned)
            print(f"[Parser] ✓ Successfully parsed JSON directly")
            return parsed
        except json.JSONDecodeError as e:
            print(f"[Parser] Direct parse failed: {str(e)}")
        
        # Try extracting JSON object with regex (greedy)
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            print(f"[Parser] Found JSON with regex, extracting...")
            json_str = json_match.group()
            print(f"[Parser] Extracted JSON: {json_str[:200]}...")
            parsed = json.loads(json_str)
            print(f"[Parser] ✓ Successfully parsed extracted JSON")
            return parsed
        
        print(f"[Parser] ✗ No JSON found in response")
        raise ValueError("No JSON found in response")
        
    except Exception as e:
        print(f"[Parser] ✗ Parse error: {str(e)}")
        raise ValueError(f"Failed to parse JSON response: {str(e)}")


def _validate_evaluation_response(data: dict) -> dict:
    """Validate and ensure evaluation response has required fields."""
    
    defaults = {
        "score": 0.0,
        "feedback": "Unable to evaluate at this time.",
        "strengths": [],
        "improvements": [],
        "technical_accuracy": 0,
        "communication": 0,
        "completeness": 0
    }
    
    result = {**defaults, **data}
    
    # Ensure types and bounds
    result["score"] = max(0, min(100, float(result.get("score", 0))))
    result["feedback"] = str(result.get("feedback", ""))[:500]
    result["strengths"] = list(result.get("strengths", []))[:5]
    result["improvements"] = list(result.get("improvements", []))[:5]
    result["technical_accuracy"] = max(0, min(100, int(result.get("technical_accuracy", 0))))
    result["communication"] = max(0, min(100, int(result.get("communication", 0))))
    result["completeness"] = max(0, min(100, int(result.get("completeness", 0))))
    
    return result


def _get_default_evaluation() -> dict:
    """Return default evaluation when evaluation fails."""
    return {
        "score": 50.0,
        "feedback": "Answer requires evaluation.",
        "strengths": ["Clear communication"],
        "improvements": ["Provide more specific examples"],
        "technical_accuracy": 50,
        "communication": 50,
        "completeness": 50
    }
