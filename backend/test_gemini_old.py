"""
Diagnostic script to test Gemini API connection.
Run this from the backend directory to verify everything is working.
"""

import asyncio
import json
from app.core.config import settings
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
try:
    model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
except Exception:
    model = None


def test_gemini_connection():
    """Test if Gemini API is working."""
    print("=" * 60)
    print("GEMINI API DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Check API key
    print(f"\n1. API Key Check:")
    if settings.GEMINI_API_KEY:
        api_key_short = settings.GEMINI_API_KEY[:10] + "***" + settings.GEMINI_API_KEY[-5:]
        print(f"   ✓ API Key is set: {api_key_short}")
    else:
        print(f"   ✗ API Key is NOT set!")
        print(f"   Please set GEMINI_API_KEY in .env file")
        return False
    
    # Test simple API call
    print(f"\n2. Simple API Call Test:")
    try:
        test_prompt = 'Return this JSON: {"test": "success"}'
        print(f"   Sending prompt: {test_prompt}")
        response = model.generate_content(test_prompt)
        print(f"   ✓ Got response: {response.text[:100]}")
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False
    
    # Test interview evaluation
    print(f"\n3. Interview Evaluation Test:")
    try:
        eval_prompt = """You are an interviewer. Evaluate this answer:
QUESTION: What is Python?
ANSWER: Python is a programming language.

Return ONLY this JSON format:
{"score": 50, "feedback": "ok", "strengths": ["basic"], "improvements": ["more details"], "technical_accuracy": 50, "communication": 50, "completeness": 50, "reasoning": "test"}"""
        print(f"   Sending evaluation prompt...")
        response = model.generate_content(eval_prompt)
        print(f"   ✓ Got response: {response.text[:150]}")
        
        # Try to parse
        text = response.text.strip()
        if text.startswith('```'):
            text = text[3:]
            if text.startswith('json'):
                text = text[4:]
            text = text.rstrip('`')
        parsed = json.loads(text)
        print(f"   ✓ Successfully parsed JSON: score={parsed.get('score')}")
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False
    
    print(f"\n" + "=" * 60)
    print("✓ ALL TESTS PASSED - Gemini is working!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_gemini_connection()
    exit(0 if success else 1)
