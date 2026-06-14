from abc import ABC, abstractmethod
import hashlib
from datetime import datetime, timezone

class JobSource(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @abstractmethod
    def fetch_raw(self) -> list[dict]:
        pass

    def normalize(self, raw_item: dict) -> dict:
        now = datetime.now(timezone.utc)
        raw_id = self._generate_id(raw_item)
        return {
            "source": self.source_name,
            "id": raw_id,
            "title": raw_item.get("title", "").strip(),
            "company": raw_item.get("company", "Unknown").strip(),
            "url": raw_item.get("url", "").strip(),
            "description": raw_item.get("description", "").strip(),
            "fetched_at": now,
            "raw_data": str(raw_item)
        }

    @staticmethod
    def _generate_id(item: dict) -> str:
        payload = f"{item.get('title','')}|{item.get('company','')}|{item.get('url','')}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]
