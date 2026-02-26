"""
Diagnostic script to test OpenRouter API connection.
Run this from the backend directory to verify everything is working.
"""

import sys
import json
from app.core.config import settings
from openai import OpenAI

# Configure OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY
)


def test_openrouter_connection():
    """Test if OpenRouter API is working."""
    
    print("=" * 60)
    print("OPENROUTER API DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Check API key
    print(f"\n1. API Key Check:")
    if settings.OPENROUTER_API_KEY:
        api_key_short = settings.OPENROUTER_API_KEY[:10] + "***" + settings.OPENROUTER_API_KEY[-5:]
        print(f"   ✓ API Key is set: {api_key_short}")
    else:
        print(f"   ✗ API Key is NOT set!")
        print(f"   Please set OPENROUTER_API_KEY in .env file")
        return False
    
    # Test API connection
    print(f"\n2. API Connection Test:")
    try:
        response = client.chat.completions.create(
            model=settings.OPENROUTER_MODEL_NAME,
            messages=[
                {"role": "user", "content": "Say 'Hello, OpenRouter is working!'"}
            ]
        )
        result = response.choices[0].message.content
        print(f"   ✓ API connection successful!")
        print(f"   Response: {result[:100]}")
    except Exception as e:
        print(f"   ✗ API connection failed!")
        print(f"   Error: {str(e)}")
        return False
    
    # Test model configuration
    print(f"\n3. Model Configuration:")
    print(f"   Model: {settings.OPENROUTER_MODEL_NAME}")
    try:
        response = client.chat.completions.create(
            model=settings.OPENROUTER_MODEL_NAME,
            messages=[
                {"role": "user", "content": "Return only: OK"}
            ]
        )
        print(f"   ✓ Model is accessible")
    except Exception as e:
        print(f"   ✗ Model test failed: {str(e)}")
        return False
    
    # Test JSON response
    print(f"\n4. JSON Response Test:")
    try:
        response = client.chat.completions.create(
            model=settings.OPENROUTER_MODEL_NAME,
            messages=[
                {"role": "user", "content": 'Return ONLY this JSON: {"status": "working", "test": true}'}
            ]
        )
        result = response.choices[0].message.content
        print(f"   Response: {result[:200]}")
        print(f"   ✓ JSON response received")
    except Exception as e:
        print(f"   ✗ JSON test failed: {str(e)}")
        return False
    
    print(f"\n" + "=" * 60)
    print("✓ ALL TESTS PASSED - OpenRouter is working!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_openrouter_connection()
    exit(0 if success else 1)
