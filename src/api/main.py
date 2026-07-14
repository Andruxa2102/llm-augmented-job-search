from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.routers import vacancies
from src.storage.db import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables if not exists"""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="LLM-Augmented Job Search API",
    description="API for an accessing LLM-filtered vacancies",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(vacancies.router)

@app.get("/")
def root():
    return {"message": "Welcome to LLM-Augmented Job Search API", "docs": "/docs"}
