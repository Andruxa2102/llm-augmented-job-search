from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class VacancyBase(BaseModel):
    title: str
    company: str
    url: str
    description: str | None = None


class VacancyResponse(VacancyBase):
    id: int
    source: str
    fetched_at: datetime

    class Config:
        from_attributes = True  # For SQLAlchemy ORM


class FilteredVacancyResponse(BaseModel):
    id: int
    title: str
    company: str
    description: str
    url: str
    decision: Literal["accept", "reject", "uncertain"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    tags: list[str]
    processed_at: datetime

    class Config:
        from_attributes = True
