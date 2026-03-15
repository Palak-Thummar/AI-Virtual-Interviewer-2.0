"""
Coding Practice API endpoints.
Provides coding problems and submission evaluation responses.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Literal
from app.services.judge0_service import evaluate_code_with_tests

router = APIRouter(prefix="/api/coding", tags=["coding"])


class ProblemExample(BaseModel):
    input: str
    output: str


class CodingProblem(BaseModel):
    id: str
    title: str
    difficulty: Literal["Easy", "Medium", "Hard"]
    description: str
    examples: List[ProblemExample]


class CodingSubmitRequest(BaseModel):
    problem_id: str
    code: str = Field(..., min_length=1)
    language: str = Field(..., min_length=1)


class CodingTestResult(BaseModel):
    input: str
    expected: str
    actual: str
    status: Literal["passed", "failed"]


class CodingSubmitResponse(BaseModel):
    passed: bool
    test_results: List[CodingTestResult]
    execution_time: str
    score: float


PROBLEMS: List[CodingProblem] = [
    CodingProblem(
        id="1",
        title="Two Sum",
        difficulty="Easy",
        description="Given an array of integers and a target integer, return indices of the two numbers such that they add up to target.",
        examples=[
            ProblemExample(
                input="nums = [2,7,11,15], target = 9",
                output="[0,1]"
            )
        ],
    ),
    CodingProblem(
        id="2",
        title="Longest Substring Without Repeating Characters",
        difficulty="Medium",
        description="Given a string, find the length of the longest substring without repeating characters.",
        examples=[
            ProblemExample(
                input="s = 'abcabcbb'",
                output="3"
            )
        ],
    ),
    CodingProblem(
        id="3",
        title="Merge k Sorted Lists",
        difficulty="Hard",
        description="Merge k sorted linked lists and return it as one sorted list.",
        examples=[
            ProblemExample(
                input="lists = [[1,4,5],[1,3,4],[2,6]]",
                output="[1,1,2,3,4,4,5,6]"
            )
        ],
    ),
]


@router.get("/problems", response_model=List[CodingProblem])
async def get_problems():
    """Return available coding problems."""
    return PROBLEMS


@router.post("/submit", response_model=CodingSubmitResponse)
async def submit_code(payload: CodingSubmitRequest):
    """Evaluate submission with Judge0 API and return deterministic test results."""
    try:
        test_results = [
            {
                "input": "nums = [2,7,11,15], target = 9",
                "expected": "[0,1]",
                "output": "[0,1]",
            },
            {
                "input": "nums = [3,2,4], target = 6",
                "expected": "[1,2]",
                "output": "[1,2]",
            },
        ]

        evaluation = await evaluate_code_with_tests(
            code=payload.code,
            language=payload.language,
            tests=test_results,
        )

        normalized_tests = [
            {
                "input": item.get("input", ""),
                "expected": item.get("expected", ""),
                "actual": item.get("actual", ""),
                "status": item.get("status", "failed"),
            }
            for item in evaluation.get("test_results", [])
        ]

        return {
            "passed": bool(evaluation.get("passed", False)),
            "test_results": normalized_tests,
            "execution_time": f"{round(float(evaluation.get('runtime_ms', 0)) / 1000, 3)}s",
            "score": float(evaluation.get("score", 0)),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate submission: {str(exc)}"
        )
