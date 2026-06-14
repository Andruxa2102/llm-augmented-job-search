from abc import ABC, abstractmethod
from typing import Any

class LLMFilterAgent(ABC):
    @abstractmethod
    def evaluate(self, vacancy: dict[str, Any]) -> dict[str, Any]: ...
