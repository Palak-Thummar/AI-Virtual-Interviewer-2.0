"""
JD vs Resume Analyzer service.
Core differentiator: Compares resume against job description for skill matching,
keyword gaps, experience mismatch, and ATS optimization.
"""

import json
import re
from typing import Dict, List
from openai import OpenAI
from app.core.config import settings, get_available_models_formatted


# Configure OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY
)


TECH_KEYWORDS = [
    "python", "java", "javascript", "typescript", "go", "golang", "c", "c++", "c#", "rust",
    "react", "angular", "vue", "next.js", "node.js", "express", "fastapi", "django", "flask", "spring",
    "html", "css", "tailwind", "bootstrap", "redux",
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "dynamodb", "oracle",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible", "jenkins", "github actions",
    "ci/cd", "git", "linux", "bash", "microservices", "rest", "graphql", "grpc", "websocket",
    "system design", "distributed systems", "scalability", "performance", "caching", "security", "oauth", "jwt",
    "machine learning", "deep learning", "nlp", "data science", "pandas", "numpy", "pytorch", "tensorflow",
    "spark", "hadoop", "airflow", "etl", "tableau", "power bi", "pytest", "unit testing", "integration testing"
]


async def analyze_resume_against_jd(
    resume_text: str,
    job_description: str
) -> Dict:
    """
    Analyze resume against job description using OpenRouter AI.
    
    This is the KEY DIFFERENTIATOR feature that:
    - Detects missing skills
    - Detects keyword gaps
    - Detects experience mismatch
    - Suggests resume improvements
    - Generates ATS optimization tips
    - Calculates ATS score from AI
    
    Args:
        resume_text: Extracted resume text
        job_description: Job description text
        
    Returns:
        Dictionary with analysis results
    """
    
    # Validate inputs
    if not resume_text or not resume_text.strip():
        print("[JD Analyzer] WARNING: Empty resume text provided")
        return _get_default_analysis_response("Empty resume text")
    
    if not job_description or not job_description.strip():
        print("[JD Analyzer] WARNING: Empty job description provided")
        return _get_default_analysis_response("Empty job description")
    
    fallback = _build_fallback_skill_analysis(resume_text, job_description)

    # First, get the analysis
    try:
        print(f"[JD Analyzer] Starting analysis with resume length: {len(resume_text)}, JD length: {len(job_description)}")
        
        # Get matched and missing skills
        matched_skills = await extract_matched_skills(resume_text, job_description)
        missing_skills = await extract_missing_skills(resume_text, job_description)
        keyword_gaps = await extract_keyword_gaps(resume_text, job_description)

        matched_skills = _merge_unique_strings(matched_skills, fallback["matched_skills"], limit=20)
        missing_skills = _merge_unique_strings(missing_skills, fallback["missing_skills"], limit=20)
        keyword_gaps = _merge_unique_strings(keyword_gaps, fallback["keyword_gaps"], limit=20)
        
        # Get ATS score directly from OpenRouter (not from formula)
        print(f"[JD Analyzer] Requesting ATS score from OpenRouter...")
        ats_score_ai = await calculate_ats_score_from_openrouter(resume_text, job_description)
        heuristic_score = float(fallback["ats_score"])

        if abs(ats_score_ai - 50.0) < 0.001:
            ats_score = heuristic_score
        else:
            ats_score = round((ats_score_ai * 0.7) + (heuristic_score * 0.3), 2)

        ats_score = min(max(float(ats_score), 0.0), 100.0)
        print(f"[JD Analyzer] OpenRouter ATS: {ats_score_ai}%, Heuristic ATS: {heuristic_score}%, Final ATS: {ats_score}%")
        
        # Get suggestions in parallel
        improvement_suggestions = await get_improvement_suggestions(resume_text, job_description)
        ats_optimization_tips = await generate_ats_optimization_tips(resume_text, job_description)
        
        # Get experience gap analysis
        experience_gap = await analyze_experience_gap(resume_text, job_description)
        
        result = {
            "ats_score": ats_score,
            "matched_skills": matched_skills[:20],
            "missing_skills": missing_skills[:20],
            "keyword_gaps": keyword_gaps[:20],
            "experience_gap": experience_gap,
            "improvement_suggestions": improvement_suggestions[:10],
            "ats_optimization_tips": ats_optimization_tips[:10]
        }
        
        print(f"[JD Analyzer] Analysis complete. Final ATS Score: {result['ats_score']}%")
        return _validate_analysis_response(result)
        
    except Exception as e:
        print(f"[JD Analyzer] ERROR in analyze_resume_against_jd: {str(e)}")
        failed_result = _get_default_analysis_response(str(e))
        failed_result["matched_skills"] = fallback.get("matched_skills", [])
        failed_result["missing_skills"] = fallback.get("missing_skills", [])
        failed_result["keyword_gaps"] = fallback.get("keyword_gaps", [])
        failed_result["ats_score"] = fallback.get("ats_score", failed_result.get("ats_score", 50.0))
        return _validate_analysis_response(failed_result)


async def generate_ats_optimization_tips(
    resume_text: str,
    job_description: str
) -> List[str]:
    """
    Generate specific ATS optimization tips.
    
    Args:
        resume_text: Resume text
        job_description: Job description
        
    Returns:
        List of ATS optimization tips
    """
    
    prompt = f"""You are an ATS optimization expert. Analyze this resume against the job description and provide 5-7 specific, actionable ATS optimization tips to improve the candidate's ATS score.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return ONLY a JSON array of strings with optimization tips. Example: ["Use keywords from job description", "Add metrics to achievements", "Use standard section headings"]

IMPORTANT: Return ONLY valid JSON array, no markdown, no explanation."""

    try:
        response = await _call_openrouter(prompt)
        tips = _parse_json_response(response)
        
        if isinstance(tips, list):
            return [str(t).strip() for t in tips[:10] if t]  # Ensure strings and limit to 10
        return ["Ensure your resume includes relevant keywords from the job description"]
    except Exception as e:
        print(f"[ATS Tips] Generation failed: {str(e)}")
        return ["Ensure your resume includes relevant keywords from the job description"]


async def calculate_ats_score_from_openrouter(
    resume_text: str,
    job_description: str
) -> float:
    """
    Calculate ATS score directly from OpenRouter AI.
    AI evaluates the resume's compatibility with the job description and provides a score.
    
    Args:
        resume_text: Resume text
        job_description: Job description
        
    Returns:
        ATS score (0-100) from OpenRouter
    """
    
    prompt = f"""You are an ATS (Applicant Tracking System) expert. Evaluate how well this resume matches the job description.

Consider:
- Keyword alignment with job requirements
- Relevant skills and experience
- Technical qualifications match
- Experience level fit
- Format and clarity (ATS readability)

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return ONLY a JSON object with the ATS score (0-100):
{{
  "ats_score": <integer 0-100>,
  "ats_reasoning": "<Brief explanation of the score>"
}}

IMPORTANT: Return ONLY valid JSON, no markdown, no explanation. The score should reflect how well the resume will pass through an ATS system and match the job requirements."""

    try:
        print(f"[ATS Calculator] Requesting ATS score from OpenRouter...")
        response = await _call_openrouter(prompt)
        print(f"[ATS Calculator] Got response...")
        
        data = _parse_json_response(response)
        
        if isinstance(data, dict):
            ats_score = data.get("ats_score", 50)
            try:
                ats_score_float = float(ats_score)
                # Ensure score is within 0-100
                final_score = min(max(ats_score_float, 0.0), 100.0)
                print(f"[ATS Calculator] OpenRouter calculated ATS score: {final_score}")
                return final_score
            except (ValueError, TypeError) as e:
                print(f"[ATS Calculator] Error converting score: {e}")
                return 50.0
        
        print(f"[ATS Calculator] Unexpected response format")
        return 50.0
        
    except Exception as e:
        print(f"[ATS Calculator] Error calculating ATS score: {str(e)}")
        return 50.0


async def extract_matched_skills(resume_text: str, job_description: str) -> List[str]:
    """Extract skills that appear in both resume and JD."""
    
    prompt = f"""Extract skills that are PRESENT in BOTH the resume AND the job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return ONLY a JSON array of skill names. Example: ["Python", "Docker", "AWS"]
Do not include soft skills, only technical skills.

IMPORTANT: Return ONLY valid JSON array, no markdown, no explanation."""
    
    try:
        response = await _call_openrouter(prompt)
        skills = _parse_json_response(response)
        
        if isinstance(skills, list):
            return [str(s).strip() for s in skills[:20] if s]
        return []
    except Exception as e:
        print(f"[Matched Skills] Extraction failed: {str(e)}")
        return []


async def extract_missing_skills(resume_text: str, job_description: str) -> List[str]:
    """Extract skills required in JD but missing from resume."""
    
    prompt = f"""Extract technical skills that are REQUIRED in the job description but MISSING or NOT MENTIONED in the resume.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return ONLY a JSON array of skill names. Example: ["Kubernetes", "GraphQL", "PostgreSQL"]
Focus on critical skills only, no soft skills.

IMPORTANT: Return ONLY valid JSON array, no markdown, no explanation."""
    
    try:
        response = await _call_openrouter(prompt)
        skills = _parse_json_response(response)
        
        if isinstance(skills, list):
            return [str(s).strip() for s in skills[:20] if s]
        return []
    except Exception as e:
        print(f"[Missing Skills] Extraction failed: {str(e)}")
        return []


async def extract_keyword_gaps(resume_text: str, job_description: str) -> List[str]:
    """Extract important keywords/technologies mentioned in JD but not in resume."""
    
    prompt = f"""Extract important keywords and technologies mentioned in the job description that are NOT in the resume.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return ONLY a JSON array of keywords/technologies. Example: ["Microservices", "CI/CD", "Cloud-native"]

IMPORTANT: Return ONLY valid JSON array, no markdown, no explanation."""
    
    try:
        response = await _call_openrouter(prompt)
        gaps = _parse_json_response(response)
        
        if isinstance(gaps, list):
            return [str(g).strip() for g in gaps[:20] if g]
        return []
    except Exception as e:
        print(f"[Keyword Gaps] Extraction failed: {str(e)}")
        return []


async def get_improvement_suggestions(resume_text: str, job_description: str) -> List[str]:
    """Get actionable resume improvement suggestions based on job match."""
    
    prompt = f"""You are a professional resume coach. Analyze this resume against the job description and provide 6-8 specific, actionable suggestions to improve the resume for this position.

Each suggestion should be concrete and implementable (e.g., "Add quantified achievements to your projects" rather than "Make it better").

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return ONLY a JSON array of improvement suggestions. Example: 
["Add quantified achievements (metrics, percentages, numbers) to your project descriptions", 
"Highlight leadership experience prominently",
"Include specific technologies and tools you've used"]

IMPORTANT: Return ONLY valid JSON array, no markdown, no explanation."""
    
    try:
        print(f"[Improvements] Requesting suggestions from OpenRouter...")
        response = await _call_openrouter(prompt)
        suggestions = _parse_json_response(response)
        
        if isinstance(suggestions, list):
            result = [str(s).strip() for s in suggestions[:15] if s]
            print(f"[Improvements] Got {len(result)} suggestions")
            return result
        
        print(f"[Improvements] Response was not a list")
        return ["Review resume for better keyword alignment", "Add more technical details to your experience"]
    except Exception as e:
        print(f"[Improvements] Suggestion failed: {str(e)}")
        return ["Review resume for better keyword alignment", "Add more technical details to your experience"]


async def analyze_experience_gap(resume_text: str, job_description: str) -> str:
    """Analyze experience level mismatch between resume and JD."""
    
    prompt = f"""Analyze if there's an experience level mismatch between the resume and job description. 
Is the candidate over-qualified, under-qualified, or a good fit?

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return ONLY a JSON object with a single key "gap" containing a brief analysis string.
Example: {{"gap": "Candidate appears to be a good fit with 5+ years of relevant experience"}}

IMPORTANT: Return ONLY valid JSON, no markdown, no explanation."""
    
    try:
        response = await _call_openrouter(prompt)
        analysis = _parse_json_response(response)
        
        gap = analysis.get("gap", "") if isinstance(analysis, dict) else str(analysis)
        return gap[:500] if gap else ""
    except Exception as e:
        print(f"[Experience Gap] Analysis failed: {str(e)}")
        return ""





async def extract_key_skills_from_jd(job_description: str) -> List[str]:
    """
    Extract key skills from job description.
    
    Args:
        job_description: Job description text
        
    Returns:
        List of key skills
    """
    
    prompt = f"""Extract the top 10 key technical skills and requirements from this job description.

JOB DESCRIPTION:
{job_description}

Return a JSON array of skills as strings. Example:
["Python", "Docker", "AWS", ...]

Only return the JSON array, no other text."""

    try:
        response = await _call_openrouter(prompt)
        skills = _parse_json_response(response)
        
        if isinstance(skills, list):
            return skills[:10]
        return []
    except Exception as e:
        return []


async def calculate_skill_match_percentage(
    resume_skills: List[str],
    jd_skills: List[str]
) -> float:
    """
    Calculate skill match percentage.
    
    Args:
        resume_skills: Skills found in resume
        jd_skills: Skills required in JD
        
    Returns:
        Match percentage (0-100)
    """
    
    if not jd_skills:
        return 0.0
    
    # Normalize and compare skills
    resume_skills_lower = [s.lower() for s in resume_skills]
    jd_skills_lower = [s.lower() for s in jd_skills]
    
    matches = sum(1 for skill in jd_skills_lower if skill in resume_skills_lower)
    percentage = (matches / len(jd_skills_lower)) * 100
    
    return min(percentage, 100.0)


# ============= HELPER FUNCTIONS =============

async def _call_openrouter(prompt: str) -> str:
    """Call OpenRouter API with prompt."""
    try:
        print(f"[OpenRouter] Calling OpenRouter with prompt length: {len(prompt)}")
        
        if not settings.OPENROUTER_API_KEY:
            raise Exception("OPENROUTER_API_KEY not configured")
        
        response = client.chat.completions.create(
            model=settings.OPENROUTER_MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        result = response.choices[0].message.content
        print(f"[OpenRouter] Success! Response length: {len(result)}")
        return result
    except Exception as e:
        print(f"[OpenRouter] API call failed: {str(e)}")
        available = get_available_models_formatted()
        print(f"[OpenRouter] Models available: {available}")
        raise Exception(f"OpenRouter API error: {str(e)}. Available models: {available}")


def _normalize_term(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _merge_unique_strings(primary: List[str], fallback: List[str], limit: int = 20) -> List[str]:
    merged: List[str] = []
    seen = set()

    for source in (primary or []), (fallback or []):
        for item in source:
            cleaned = str(item).strip()
            if not cleaned:
                continue
            key = _normalize_term(cleaned)
            if key in seen:
                continue
            seen.add(key)
            merged.append(cleaned)
            if len(merged) >= limit:
                return merged

    return merged


def _extract_technical_terms_from_text(text: str) -> List[str]:
    content = str(text or "").lower()
    found = []
    seen = set()

    for keyword in TECH_KEYWORDS:
        token = keyword.lower().strip()
        if not token:
            continue

        pattern = r"(?<!\w)" + re.escape(token) + r"(?!\w)"
        if re.search(pattern, content):
            normalized = _normalize_term(token)
            if normalized in seen:
                continue
            seen.add(normalized)
            found.append(keyword)

    return found


def _build_fallback_skill_analysis(resume_text: str, job_description: str) -> dict:
    resume_terms = _extract_technical_terms_from_text(resume_text)
    jd_terms = _extract_technical_terms_from_text(job_description)

    resume_set = {_normalize_term(term) for term in resume_terms}

    matched = []
    missing = []
    for term in jd_terms:
        normalized = _normalize_term(term)
        if normalized in resume_set:
            matched.append(term)
        else:
            missing.append(term)

    if jd_terms:
        coverage = len(matched) / len(jd_terms)
        heuristic_ats = round(35.0 + (coverage * 60.0), 2)
    else:
        heuristic_ats = 50.0

    return {
        "ats_score": min(max(float(heuristic_ats), 0.0), 100.0),
        "matched_skills": matched[:20],
        "missing_skills": missing[:20],
        "keyword_gaps": missing[:20]
    }


def _parse_json_response(response: str) -> dict:
    """Parse JSON from AI response - aggressive extraction."""
    try:
        # Clean up the response - remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]  # Remove opening ```
            if cleaned.startswith('json'):
                cleaned = cleaned[4:]  # Remove 'json' if present
            if cleaned.startswith('\n'):
                cleaned = cleaned[1:]
            cleaned = cleaned.rstrip('`')
        cleaned = cleaned.strip()
        
        # Try direct parse first
        try:
            parsed = json.loads(cleaned)
            print(f"[Parser] Successfully parsed JSON. Type: {type(parsed).__name__}")
            return parsed
        except json.JSONDecodeError:
            pass
        
        # Try extracting JSON object (greedy)
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            print(f"[Parser] Found JSON object")
            parsed = json.loads(json_match.group())
            return parsed
        
        # Try extracting JSON array (greedy)
        json_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if json_match:
            print(f"[Parser] Found JSON array")
            parsed = json.loads(json_match.group())
            return parsed
        
        print(f"[Parser] Unable to extract JSON. Response: {cleaned[:100]}...")
        raise ValueError("No JSON found in response")
        
    except Exception as e:
        print(f"[Parser] Parsing failed: {str(e)}")
        raise ValueError(f"Invalid JSON response: {str(e)}")


def _validate_analysis_response(data: dict) -> dict:
    """Validate and ensure analysis response has all required fields."""
    
    defaults = {
        "ats_score": 50.0,  # Default to 50 instead of 0 for better UX
        "matched_skills": [],
        "missing_skills": [],
        "keyword_gaps": [],
        "experience_gap": "",
        "improvement_suggestions": [],
        "ats_optimization_tips": []
    }
    
    print(f"[Validator] Input data type: {type(data).__name__}")
    
    # If data is not a dict, return defaults
    if not isinstance(data, dict):
        print(f"[Validator] WARNING: Data is not a dict, returning defaults")
        return defaults
    
    print(f"[Validator] Input data keys: {list(data.keys())}")
    print(f"[Validator] Raw ATS score value: {data.get('ats_score')} (type: {type(data.get('ats_score'))})")
    
    # Merge with defaults, keeping provided values
    result = {**defaults, **data}
    
    # Ensure types are correct - handle ATS score conversion with better error handling
    ats_score_raw = result.get("ats_score", 50)
    try:
        ats_score_float = float(ats_score_raw) if ats_score_raw is not None else 50.0
        # Clamp to 0-100
        result["ats_score"] = min(max(ats_score_float, 0.0), 100.0)
    except (ValueError, TypeError) as e:
        print(f"[Validator] ERROR converting ATS score: {str(e)}. Raw value: {ats_score_raw}")
        result["ats_score"] = 50.0
    
    result["matched_skills"] = list(result.get("matched_skills", []))[:20]
    result["missing_skills"] = list(result.get("missing_skills", []))[:20]
    result["keyword_gaps"] = list(result.get("keyword_gaps", []))[:20]
    result["experience_gap"] = str(result.get("experience_gap", ""))
    result["improvement_suggestions"] = list(result.get("improvement_suggestions", []))[:10]
    result["ats_optimization_tips"] = list(result.get("ats_optimization_tips", []))[:10]
    
    print(f"[Validator] Final ATS score: {result['ats_score']}")
    
    return result


def _get_default_analysis_response(error: str) -> dict:
    """Return default response when analysis fails."""
    print(f"[Default Response] Returning fallback response due to: {error}")
    return {
        "ats_score": 50.0,  # Return 50 as neutral fallback instead of 0
        "matched_skills": [],
        "missing_skills": [],
        "keyword_gaps": [],
        "experience_gap": f"Could not complete detailed analysis: {error}",
        "improvement_suggestions": ["Ensure resume and job description are properly provided", "Check for keyword alignment"],
        "ats_optimization_tips": ["Use industry-standard keywords", "Format resume clearly with proper sections"]
    }
