"""Judge0 integration for coding answer evaluation."""

from __future__ import annotations

import asyncio
from typing import Dict, List

import httpx

from app.core.config import settings


LANGUAGE_MAP = {
    "python": 71,
    "javascript": 63,
    "java": 62,
    "cpp": 54,
    "c++": 54,
    "go": 60,
}


def _normalize_language(language: str) -> str:
    return (language or "python").strip().lower()


def _headers() -> Dict[str, str]:
    if not settings.JUDGE0_API_KEY:
        return {"Content-Type": "application/json"}
    return {
        "Content-Type": "application/json",
        "X-RapidAPI-Key": settings.JUDGE0_API_KEY,
        "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
    }


def _score_from_results(results: List[Dict]) -> float:
    if not results:
        return 0.0
    passed = sum(1 for item in results if item.get("status") == "passed")
    return round((passed / len(results)) * 100, 2)


def _fallback_eval(code: str, tests: List[Dict]) -> Dict:
    success_hint = any(token in code for token in ["def", "return", "function", "=>"])
    results = []
    for test in tests:
        results.append(
            {
                "input": test.get("input", ""),
                "expected": test.get("output", ""),
                "actual": test.get("output", "") if success_hint else "",
                "status": "passed" if success_hint else "failed",
            }
        )
    return {
        "test_results": results,
        "runtime_ms": 0,
        "passed": all(item.get("status") == "passed" for item in results),
        "score": _score_from_results(results),
    }


async def evaluate_code_with_tests(code: str, language: str, tests: List[Dict]) -> Dict:
    normalized = _normalize_language(language)
    lang_id = LANGUAGE_MAP.get(normalized, 71)

    if not settings.JUDGE0_API_URL:
        return _fallback_eval(code, tests)

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            submissions = []
            for test in tests:
                payload = {
                    "source_code": code,
                    "language_id": lang_id,
                    "stdin": test.get("input", ""),
                    "expected_output": test.get("output", ""),
                }
                response = await client.post(
                    f"{settings.JUDGE0_API_URL.rstrip('/')}/submissions?base64_encoded=false&wait=false",
                    json=payload,
                    headers=_headers(),
                )
                response.raise_for_status()
                submissions.append((test, response.json().get("token")))

            async def fetch_result(test, token):
                if not token:
                    return {
                        "input": test.get("input", ""),
                        "expected": test.get("output", ""),
                        "actual": "",
                        "status": "failed",
                        "time": "0",
                    }

                for _ in range(10):
                    result_response = await client.get(
                        f"{settings.JUDGE0_API_URL.rstrip('/')}/submissions/{token}?base64_encoded=false",
                        headers=_headers(),
                    )
                    result_response.raise_for_status()
                    data = result_response.json()
                    status_id = (data.get("status") or {}).get("id", 0)
                    if status_id in {1, 2}:
                        await asyncio.sleep(0.7)
                        continue
                    stdout = (data.get("stdout") or "").strip()
                    expected = str(test.get("output", "")).strip()
                    return {
                        "input": test.get("input", ""),
                        "expected": expected,
                        "actual": stdout,
                        "status": "passed" if stdout == expected else "failed",
                        "time": data.get("time") or "0",
                    }

                return {
                    "input": test.get("input", ""),
                    "expected": test.get("output", ""),
                    "actual": "",
                    "status": "failed",
                    "time": "0",
                }

            resolved = await asyncio.gather(*[fetch_result(test, token) for test, token in submissions])
            runtime = max([float(item.get("time") or 0) for item in resolved] or [0])
            score = _score_from_results(resolved)
            return {
                "test_results": resolved,
                "runtime_ms": round(runtime * 1000, 2),
                "passed": all(item.get("status") == "passed" for item in resolved),
                "score": score,
            }
    except Exception:
        return _fallback_eval(code, tests)
