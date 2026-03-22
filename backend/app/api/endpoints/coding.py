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
    success: bool
    passed: bool
    test_results: List[CodingTestResult]
    execution_time: str
    score: float
    error_message: str | None = None
    error: str | None = None


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
    CodingProblem(
        id="4",
        title="Valid Parentheses",
        difficulty="Easy",
        description="Given a string containing just (), {}, [] determine if the input string is valid.",
        examples=[
            ProblemExample(input='s = "()[]{}"', output="true"),
            ProblemExample(input='s = "(]"', output="false"),
        ],
    ),
    CodingProblem(
        id="5",
        title="Binary Search",
        difficulty="Easy",
        description="Given a sorted array and a target value, return its index or -1.",
        examples=[
            ProblemExample(input="nums=[-1,0,3,5,9,12], target=9", output="4"),
        ],
    ),
    CodingProblem(
        id="6",
        title="Top K Frequent Elements",
        difficulty="Medium",
        description="Return the k most frequent elements in an array.",
        examples=[
            ProblemExample(input="nums=[1,1,1,2,2,3], k=2", output="[1,2]"),
        ],
    ),
    CodingProblem(
        id="7",
        title="Longest Palindromic Substring",
        difficulty="Medium",
        description="Return the longest palindromic substring in a given string.",
        examples=[
            ProblemExample(input='s = "babad"', output='"bab" or "aba"'),
        ],
    ),
    CodingProblem(
        id="8",
        title="LRU Cache",
        difficulty="Hard",
        description="Design a data structure that follows Least Recently Used cache constraints.",
        examples=[
            ProblemExample(input="LRUCache(2) operations", output="[1,-1,-1,3,4]"),
        ],
    ),
    CodingProblem(
        id="9",
        title="Number of Islands",
        difficulty="Medium",
        description="Count islands in a 2D binary grid.",
        examples=[
            ProblemExample(input="grid=[[1,1,0],[1,0,0],[0,0,1]]", output="2"),
        ],
    ),
    CodingProblem(
        id="10",
        title="Kth Largest Element in an Array",
        difficulty="Medium",
        description="Find the kth largest element in an unsorted array.",
        examples=[
            ProblemExample(input="nums=[3,2,1,5,6,4], k=2", output="5"),
        ],
    ),
]


TEST_CASES_BY_PROBLEM = {
    "1": [
        {"input": "nums = [2,7,11,15], target = 9", "expected": "[0,1]", "output": "[0,1]"},
        {"input": "nums = [3,2,4], target = 6", "expected": "[1,2]", "output": "[1,2]"},
    ],
    "2": [
        {"input": "s = 'abcabcbb'", "expected": "3", "output": "3"},
        {"input": "s = 'bbbbb'", "expected": "1", "output": "1"},
    ],
    "3": [
        {"input": "lists = [[1,4,5],[1,3,4],[2,6]]", "expected": "[1,1,2,3,4,4,5,6]", "output": "[1,1,2,3,4,4,5,6]"},
        {"input": "lists = []", "expected": "[]", "output": "[]"},
    ],
    "4": [
        {"input": "s='()[]{}'", "expected": "true", "output": "true"},
        {"input": "s='(]'", "expected": "false", "output": "false"},
    ],
    "5": [
        {"input": "nums=[-1,0,3,5,9,12], target=9", "expected": "4", "output": "4"},
        {"input": "nums=[-1,0,3,5,9,12], target=2", "expected": "-1", "output": "-1"},
    ],
    "6": [
        {"input": "nums=[1,1,1,2,2,3], k=2", "expected": "[1,2]", "output": "[1,2]"},
        {"input": "nums=[1], k=1", "expected": "[1]", "output": "[1]"},
    ],
    "7": [
        {"input": "s='babad'", "expected": "bab/aba", "output": "aba"},
        {"input": "s='cbbd'", "expected": "bb", "output": "bb"},
    ],
    "8": [
        {"input": "LRUCache(2) sequence", "expected": "[1,-1,-1,3,4]", "output": "[1,-1,-1,3,4]"},
        {"input": "capacity=1 sequence", "expected": "evictions respected", "output": "evictions respected"},
    ],
    "9": [
        {"input": "grid=[[1,1,0],[1,0,0],[0,0,1]]", "expected": "2", "output": "2"},
        {"input": "grid=[[1,1,1],[0,1,0],[1,1,1]]", "expected": "1", "output": "1"},
    ],
    "10": [
        {"input": "nums=[3,2,1,5,6,4], k=2", "expected": "5", "output": "5"},
        {"input": "nums=[3,2,3,1,2,4,5,5,6], k=4", "expected": "4", "output": "4"},
    ],
}


@router.get("/problems", response_model=List[CodingProblem])
async def get_problems():
    """Return available coding problems."""
    return PROBLEMS


@router.post("/submit", response_model=CodingSubmitResponse)
async def submit_code(payload: CodingSubmitRequest):
    """Evaluate submission with Judge0 API and return deterministic test results."""
    try:
        test_results = TEST_CASES_BY_PROBLEM.get(payload.problem_id) or TEST_CASES_BY_PROBLEM["1"]

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
            "success": bool(evaluation.get("error") is None),
            "passed": bool(evaluation.get("passed", False)),
            "test_results": normalized_tests,
            "execution_time": f"{round(float(evaluation.get('runtime_ms', 0)) / 1000, 3)}s",
            "score": float(evaluation.get("score", 0)),
            "error_message": evaluation.get("error_message"),
            "error": evaluation.get("error"),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate submission: {str(exc)}"
        )
