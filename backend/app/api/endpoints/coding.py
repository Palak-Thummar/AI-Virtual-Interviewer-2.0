"""
Coding Practice API endpoints.
Provides coding problems and submission evaluation responses.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Literal

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
    """Mock submission evaluator for coding practice."""
    try:
        has_code = bool(payload.code.strip())
        likely_pass = has_code and ("solve" in payload.code or "def" in payload.code or "function" in payload.code)

        test_results = [
            {
                "input": "nums = [2,7,11,15], target = 9",
                "expected": "[0,1]",
                "actual": "[0,1]" if likely_pass else "[]",
                "status": "passed" if likely_pass else "failed",
            },
            {
                "input": "nums = [3,2,4], target = 6",
                "expected": "[1,2]",
                "actual": "[1,2]" if likely_pass else "[]",
                "status": "passed" if likely_pass else "failed",
            },
        ]

        return {
            "passed": all(item["status"] == "passed" for item in test_results),
            "test_results": test_results,
            "execution_time": "0.12s",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate submission: {str(exc)}"
        )
