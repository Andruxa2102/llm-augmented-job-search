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

    def normalize(self, item: dict) -> dict:
        return {
            "source_id": self._generate_source_id(item),
            "source": self.source_name,
            "title": item.get("title", "").strip(),
            "company": item.get("company", "").strip(),
            "url": item.get("url", "").strip(),
            "description": item.get("description", "").strip(),
            "raw_data": str(item),
            "fetched_at": datetime.now(timezone.utc),
        }

    @staticmethod
    def _generate_source_id(item: dict) -> str:
        url = item.get("url", "").strip()
        content = url if url else f"{item.get('title')}|{item.get('company')}"
        return hashlib.md5(content.encode()).hexdigest()
