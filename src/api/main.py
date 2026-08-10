from contextlib import asynccontextmanager
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi_offline import FastAPIOffline
from src.storage.db import Base, engine
from src.api.routers import vacancies, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables if not exists"""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPIOffline(
    title="LLM-Augmented Job Search API",
    description="API for an accessing LLM-filtered vacancies",
    version="0.1.0",
    lifespan=lifespan
)


app.include_router(auth.router)
app.include_router(vacancies.router)


static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", tags=["root"])
def root():
    from fastapi.responses import FileResponse
    return FileResponse(static_dir / "index.html")