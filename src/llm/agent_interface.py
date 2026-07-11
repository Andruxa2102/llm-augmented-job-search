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
    def evaluate_batch(self, vacancies: list[dict[str, Any]]) -> list[LLMEvaluationResult]:
        """Evaluate multiple vacancies in batches. For single vacancy, call: evaluate_batch([vacancy])[0]"""
        pass