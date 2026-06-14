from sqlalchemy import String, Boolean, Float, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from src.storage.db import Base

class RawVacancy(Base):
    __tablename__ = "raw_vacancies"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    source: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    raw_data: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime)

class FilteredVacancy(Base):
    __tablename__ = "filtered_vacancies"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(16))
    llm_pass: Mapped[bool] = mapped_column(Boolean)
    confidence: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    tags: Mapped[str] = mapped_column(Text)  # хранит JSON-массив строкой
    processed_at: Mapped[datetime] = mapped_column(DateTime)
