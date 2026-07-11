import json, logging, yaml
from json import JSONDecodeError
from pathlib import Path
from time import sleep
from ollama import chat, ResponseError
from pydantic import BaseModel, ValidationError
from src.llm.agent_interface import LLMFilterAgent, LLMEvaluationResult

logger = logging.getLogger(__name__)

class LLMBatchResponse(BaseModel):
    results: list[LLMEvaluationResult]

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

    def evaluate_batch(self, vacancies: list[dict]) -> list[LLMEvaluationResult]:
        """evaluates vacancies in batches"""
        all_results = []

        for i in range(0, len(vacancies), self.batch_size):
            batch = vacancies[i:i + self.batch_size]
            logger.info(f"Processing batch {i // self.batch_size + 1}: {len(batch)} vacancies")

            batch_results = self._process_batch(batch)
            all_results.extend(batch_results)

            if i + self.batch_size < len(vacancies):
                sleep(1.0)

        return all_results

    def _process_batch(self, batch: list[dict]) -> list[LLMEvaluationResult]:
        """Data processing by LLM"""
        try:
            response = chat(
                model = self.model,
                messages = self._build_prompt(batch),
                format = LLMBatchResponse.model_json_schema(),
                options = {"temperature": self.cfg.get("temperature", 0.1)}
            )

            if hasattr(response, 'message'):
                raw_content = response.message.content
            else:
                raw_content = response['message']['content']

            json_data = json.loads(raw_content)
            validated_batch = LLMBatchResponse.model_validate(json_data)

            return validated_batch.results

        except ResponseError as e:
            logger.error(f"Ollama API error (Status {e.status_code}): {e.error}. Using fallback.")
            return self._fallback_response(f"Ollama API error: {e.error}", len(batch))

        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Ollama connection failed: {e}. Using fallback.")
            return self._fallback_response("Connection error", len(batch))

        except JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON: {e}. Raw text was: {raw_content[:200]}")
            return self._fallback_response("Invalid JSON format", len(batch))

        except ValidationError as e:
            logger.warning(f"Pydantic validation failed: {e.errors()}. Using fallback.")
            return self._fallback_response("Pydantic structure mismatch", len(batch))

        except Exception as e:
            logger.error(f"Unexpected pipeline error: {e}", exc_info=True)
            return self._fallback_response(f"Unexpected error: {str(e)}", len(batch))


    @staticmethod
    def _build_prompt(batch: list[dict]) -> list[dict[str, str]]:
        """send one request with list of vacancies"""

        # Prompt for a batch
        vacancy_list = "\n\n".join([
            f"### Vacancy {i + 1}:\nTitle: {v['title']}\nCompany: {v['company']}\nDescription: {v['description']}"
            for i, v in enumerate(batch)
        ])

        system_text = f"""You are an expert HR assistant specializing in Data Engineering recruitment.
TASK: I will give you {len(batch)} vacancies. 
Evaluate all vacancies by conditions:

Condition A (Role & Grade Match):
- The job title contains keywords: Data Engineer, Analytics Engineer, ETL Developer, DWH Developer, Database Developer, DB Developer, Database Engineer, Data Platform Engineer.
- AND the grade is suitable: Middle, Middle+, Middle/Senior, Middle+/Senior, Junior/Middle, Junior+/Middle, OR NOT specified.
(Note: Reject only if it is EXCLUSIVELY pure Lead, Team Lead, Architect, Trainee, or Intern).

Condition B (Tech Stack / Activity Match):
- The vacancy description explicitly mentions ANY data engineering activity or tools: Data pipelines, ETL, ELT, SQL optimization, data processing.

Set decision to "reject" in all other cases (if Condition A or Condition B is false).


IMPORTANT: You MUST return a JSON ARRAY with exactly {len(batch)} objects, one per vacancy.
Even if there is only 1 vacancy
[
    {{"decision": "accept|reject", "confidence": 0.0-1.0, "reason": "string in Russian", "tags": ["skill1, "skill2""]}},
    ... (one object per vacancy, in the same order)
]
"""

        role_text = f"""Vacancies for your validation:
        
{vacancy_list}
"""

        out = [
            {
                "role": "system",
                "content": system_text
            },
            {
                "role": "user",
                "content": role_text
            }
        ]


        return out

    @staticmethod
    def _fallback_response(reason: str, size: int) -> list[LLMEvaluationResult]:
        """Graceful degradation: fallback to a safe result on LLM failure"""
        return [LLMEvaluationResult.model_validate({
            "decision": "uncertain",
            "confidence": 0.0,
            "reason": f"LLM unavailable: {reason}",
            "tags": ["llm_error"]
        })] * size