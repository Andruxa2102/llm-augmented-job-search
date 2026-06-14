import json, logging, yaml
from typing import Any
import ollama
from src.llm.agent_interface import LLMFilterAgent

logger = logging.getLogger(__name__)

class PurePythonFilterAgent(LLMFilterAgent):
    def __init__(self, cfg_path: str = "../config/llm.yaml"):
        with open(cfg_path) as f: self.cfg = yaml.safe_load(f)

    def evaluate(self, vacancy: dict[str, Any]) -> dict[str, Any]:
        prompt = (f"Vacancy: {vacancy['title']}\nCompany: {vacancy['company']}\n"
                  f"Description: {vacancy['description']}\n\n"
                  f"Return ONLY JSON matching the schema. Is it suitable for Python/Data Engineering?")
        try:
            resp = ollama.chat(model=self.cfg["model"], messages=[{"role":"user","content":prompt}],
                               format=self.cfg["json_schema"])
            res = json.loads(resp["message"]["content"])
            if not {"pass","confidence","reason","tags"}.issubset(res): raise ValueError("Bad schema")
            return {**res, "model": self.cfg["model"]}
        except Exception as e:
            logger.error(f"LLM failed: {e}")
            return {"pass": False, "confidence": 0.0, "reason": f"Error: {e}", "tags": [], "model": "fallback"}
