from enum import Enum as PyEnum
from sqlalchemy import Float, DateTime, Text, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from src.storage.db import Base

class Decisions(PyEnum):
    accept = "accept"
    reject = "reject"
    uncertain = "uncertain"

class RawVacancy(Base):
    __tablename__ = "raw_vacancies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    source: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    company: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    raw_data: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<RawVacancy(id={self.id}, title='{self.title[:30]}...', company='{self.company}')>"

class FilteredVacancy(Base):
    __tablename__ = "filtered_vacancies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    decision: Mapped[Decisions] = mapped_column(Enum(Decisions, native_enum=False), nullable=False)
    confidence: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    tags: Mapped[str] = mapped_column(Text)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<FilteredVacancy(id={self.id}, decision={self.decision.value}, confidence={self.confidence:.2f})>"
