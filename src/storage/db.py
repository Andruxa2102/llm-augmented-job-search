from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent.parent

class DBSettings(BaseSettings):
    db_url: str
    model_config = {
        "env_file": BASE_DIR / ".env",
        "extra": "ignore"
    }

class Base(DeclarativeBase):
    pass

settings = DBSettings()

if settings.db_url.startswith("sqlite:///"):
    db_path_str = settings.db_url.replace("sqlite:///", "")
    if not Path(db_path_str).is_absolute():
        db_path = (BASE_DIR / db_path_str).resolve()
        final_db_url = f"sqlite:///{db_path}"
    else:
        final_db_url = settings.db_url
else:
    final_db_url = settings.db_url


db_file_path = Path(final_db_url.replace("sqlite:///", ""))
db_file_path.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(final_db_url, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
