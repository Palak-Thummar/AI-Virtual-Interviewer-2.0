"""Judge0 integration for coding answer evaluation."""

from __future__ import annotations

import asyncio
from typing import Dict, List

import httpx

from app.core.config import settings


LANGUAGE_MAP = {
    "python": 71,
    "py": 71,
    "javascript": 63,
    "js": 63,
    "typescript": 74,
    "ts": 74,
    "java": 62,
    "cpp": 54,
    "c++": 54,
    "c": 50,
    "go": 60,
    "csharp": 51,
    "c#": 51,
    "rust": 73,
}


def _normalize_language(language: str) -> str:
    return (language or "python").strip().lower()


def _headers() -> Dict[str, str]:
    api_url = (settings.JUDGE0_API_URL or "").lower()
    if not settings.JUDGE0_API_KEY or "rapidapi" not in api_url:
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
    message = "Code execution service unavailable"
    results = []
    for test in tests:
        results.append(
            {
                "input": test.get("input", ""),
                "expected": test.get("output", ""),
                "actual": message,
                "status": "failed",
            }
        )
    return {
        "test_results": results,
        "runtime_ms": 0,
        "passed": False,
        "score": 0.0,
        "error_message": message,
        "error": message,
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
                        "status_id": 0,
                        "stderr": "No submission token returned by Judge0",
                        "compile_output": "",
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
                    stderr = (data.get("stderr") or "").strip()
                    compile_output = (data.get("compile_output") or "").strip()
                    expected = str(test.get("output", "")).strip()
                    passed = bool(status_id == 3 and not stderr and not compile_output and stdout == expected)
                    actual_value = stdout
                    if compile_output:
                        actual_value = f"Compilation Error: {compile_output}"
                    elif stderr:
                        actual_value = f"Runtime Error: {stderr}"
                    return {
                        "input": test.get("input", ""),
                        "expected": expected,
                        "actual": actual_value,
                        "status": "passed" if passed else "failed",
                        "time": data.get("time") or "0",
                        "status_id": status_id,
                        "stderr": stderr,
                        "compile_output": compile_output,
                    }

                return {
                    "input": test.get("input", ""),
                    "expected": test.get("output", ""),
                    "actual": "",
                    "status": "failed",
                    "time": "0",
                    "status_id": 0,
                    "stderr": "Timed out waiting for Judge0 result",
                    "compile_output": "",
                }

            resolved = await asyncio.gather(*[fetch_result(test, token) for test, token in submissions])
            runtime = max([float(item.get("time") or 0) for item in resolved] or [0])
            score = _score_from_results(resolved)
            compile_errors = [item.get("compile_output") for item in resolved if item.get("compile_output")]
            runtime_errors = [item.get("stderr") for item in resolved if item.get("stderr")]
            error_message = ""
            if compile_errors:
                error_message = f"Compilation failed: {compile_errors[0]}"
            elif runtime_errors:
                error_message = f"Runtime failed: {runtime_errors[0]}"
            return {
                "test_results": resolved,
                "runtime_ms": round(runtime * 1000, 2),
                "passed": bool(all(item.get("status") == "passed" for item in resolved) and not error_message),
                "score": score if not error_message else 0.0,
                "error_message": error_message or None,
            }
    except Exception:
        return _fallback_eval(code, tests)
