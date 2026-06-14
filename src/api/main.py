from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from src.storage.db import SessionLocal
from src.storage.models import FilteredVacancy

app = FastAPI(title="LLM augmented job search", version="1.0.0")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

class VacancyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    company: str
    url: str
    reason: str
    confidence: float
    processed_at: datetime

@app.get("/api/v1/vacancies", response_model=list[VacancyOut])
def get_vacancies(db: Session = Depends(get_db)):
    return db.query(FilteredVacancy).filter(FilteredVacancy.llm_pass == True)\
        .order_by(FilteredVacancy.processed_at.desc()).limit(50).all()
