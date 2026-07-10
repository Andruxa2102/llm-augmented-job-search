import json, logging, yaml
from pathlib import Path
from time import sleep
from typing import Any
from httpx import Client, RequestError
from src.llm.agent_interface import LLMFilterAgent, LLMEvaluationResult

logger = logging.getLogger(__name__)

class PurePythonFilterAgent(LLMFilterAgent):
    def __init__(self):

        config_path = Path(__file__).parent.parent.parent / "config" / "llm.yaml"

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.cfg = yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning("llm.yaml not found, using defaults")
            self.cfg = {"model": "qwen2.5:3b", "temperature": 0.1, "timeout_s": 30}

        self.base_url = self.cfg.get("base_url", "http://localhost:11434")
        self.model = self.cfg.get("model", "qwen2.5:3b")
        self.timeout = self.cfg.get("timeout_s", 30)
        self.batch_size = 10

    def evaluate(self, vacancy: dict[str, Any]) -> LLMEvaluationResult:
        """evaluates vacancies"""

        prompt = self._build_prompt(vacancy)

        try:
            with Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": self.cfg.get("temperature", 0.1)
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()

                llm_response = json.loads(result["response"])
                decision = llm_response.get("decision", "")

                if decision not in ["accept", "reject"]:
                    return self._fallback_response("Invalid decision value")

                confidence = float(llm_response.get("confidence", 0.0))
                if confidence < 0.0 or confidence > 1.0:
                    return self._fallback_response("Invalid confidence value")

                # Result Validation (Preventing Hallucinations)
                return LLMEvaluationResult.model_validate({
                    "decision": decision,
                    "confidence": max(0.0, min(1.0, float(llm_response.get("confidence", 0.0)))),
                    "reason": str(llm_response.get("reason", ""))[:200],
                    "tags": llm_response.get("tags", [])
                })

        except RequestError as e:
            logger.warning(f"Ollama connection failed: {e}. Using fallback.")
            return self._fallback_response("Connection error")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}. Using fallback.")
            return self._fallback_response("Invalid JSON format")
        except Exception as e:
            logger.error(f"Unexpected LLM error: {e}. Using fallback.")
            return self._fallback_response("Unexpected error")

    def evaluate_batch(self, vacancies: list[dict]) -> list[LLMEvaluationResult]:
        """evaluates vacancies in batches"""
        results = []

        for i in range(0, len(vacancies), self.batch_size):
            batch = vacancies[i:i + self.batch_size]
            logger.info(f"Processing batch {i // self.batch_size + 1}: {len(batch)} vacancies")

            batch_results = self._build_batch_prompt(batch)
            results.extend(batch_results)

            if i + self.batch_size < len(vacancies):
                sleep(1.0)

        return results

    @staticmethod
    def _build_batch_prompt(batch: list[dict]) -> str:
        """send one request with list of vacancies"""

        # Prompt for a batch
        vacancy_list = "\n\n".join([
            f"### Vacancy {i + 1}:\nTitle: {v['title']}\nCompany: {v['company']}\nDescription: {v['description']}"
            for i, v in enumerate(batch)
        ])

        return f"""You are an expert HR assistant specializing in Data Engineering recruitment. 
Evaluate these {len(batch)} vacancies.

{vacancy_list}

Respond ONLY with a JSON array matching this schema:
[
    {{"decision": "accept|reject", "confidence": 0.0-1.0, "reason": "string in Russian", "tags": ["skill1, "skill2""]}},
    ... (one object per vacancy, in the same order)
]
"""

    @staticmethod
    def _build_prompt(vacancy: dict) -> str:
        return f"""You are an expert HR assistant specializing in Data Engineering recruitment.

    TASK: Evaluate if vacancy is a STRONG MATCH for a Data Engineer, DWH Developer, ETL Developer, Analytics Engineer role
    
    REJECT in all cases where:
    - Explicit requirement of 5+ years experience
    - Senior/Lead/Junior/Trainee/Intern grade explicitly required
    
    ACCEPT if not REJECT clause and all of these are present:
    - Role contains: Data Engineer, Analytics Engineer, Data Developer, DWH Developer, ETL Developer
    - Description mentions pipeline development, data processing, SQL query optimizing
    - Experience requirement is 0-4 years OR not specified
    - Middle or not specified grade
    
    Examples:
    ACCEPT: "Дата-инженер — Опыт от 3 лет. SQL, Python, ETL-пайплайны"
    ACCEPT: "DWH Developer — Знание SQL, проектирование хранилищ"
    REJECT: "Senior Data Engineer — 5+ лет опыта, управление командой"
    REJECT: "Frontend Developer — React, TypeScript"
    REJECT: "ML Engineer — PyTorch, обучение моделей"

    Respond ONLY with valid JSON matching this schema:
    {{
        "decision": "accept" | "reject",
        "confidence": float (0.0 to 1.0),
        "reason": "string in Russian, max 2 sentences",
        "tags": ["skill1", "skill2"]
    }}
    """

    @staticmethod
    def _fallback_response(reason: str) -> LLMEvaluationResult:
        """Graceful degradation: fallback to a safe result on LLM failure"""
        return LLMEvaluationResult.model_validate({
            "decision": "uncertain",
            "confidence": 0.0,
            "reason": f"LLM unavailable: {reason}",
            "tags": ["llm_error"]
        })