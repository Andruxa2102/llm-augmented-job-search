from contextlib import asynccontextmanager
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi_offline import FastAPIOffline
from fastapi.middleware.cors import CORSMiddleware

from src.storage.db import Base, engine
from src.api.routers import vacancies, auth
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add Security headers to all responses"""
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "frame-ancestors 'none'"
        )
        return response

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

origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.include_router(auth.router)
app.include_router(vacancies.router)


static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", tags=["root"])
def root():
    from fastapi.responses import FileResponse
    return FileResponse(static_dir / "index.html")