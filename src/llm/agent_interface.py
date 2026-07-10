from abc import ABC, abstractmethod
from typing import Any, Literal
from pydantic import BaseModel


class LLMEvaluationResult(BaseModel):
    decision:   Literal["accept", "reject", "uncertain"]
    confidence: float  # 0.0 to 1.0
    reason:     str        # in Russian
    tags:       list[str]

class LLMFilterAgent(ABC):
    @abstractmethod
    def evaluate(self, vacancy: dict[str, Any]) -> LLMEvaluationResult:
        """Evaluate a vacancy and determine its suitability"""
        pass

    def evaluate_batch(self, vacancies: list[dict[str, Any]]) -> list[LLMEvaluationResult]:
        """Evaluate multiple vacancies (can be overridden for optimization)"""
        return [self.evaluate(v) for v in vacancies]