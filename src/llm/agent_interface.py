from abc import ABC, abstractmethod
from typing import Any, TypedDict, Literal


class LLMEvaluationResult(TypedDict):
    decision: Literal["accept", "reject", "uncertain"]
    confidence: float  # 0.0 to 1.0
    reason: str        # in Russian
    tags: list[str]

class LLMFilterAgent(ABC):
    @abstractmethod
    def evaluate(self, vacancy: dict[str, Any]) -> LLMEvaluationResult:
        """Evaluate a vacancy and determine its suitability
        Returns:
            {"pass": bool, "confidence": float, "reason": str, "tags": list[str]}"""
        pass