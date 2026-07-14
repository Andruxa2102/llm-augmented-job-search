import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from pydantic_settings import BaseSettings

class DBSettings(BaseSettings):
    db_url: str
    model_config = {
        "env_file": Path(__file__).parent.parent.parent / ".env",
        "extra": "ignore"
    }

class Base(DeclarativeBase):
    pass

settings = DBSettings()
os.makedirs(Path(__file__).parent.parent.parent / "data", exist_ok=True)

engine = create_engine(settings.db_url, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()