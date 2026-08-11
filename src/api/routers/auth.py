from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from src.api.rate_limiter import limiter
from src.storage.db import get_db
from src.storage.models import User
from src.api.security import verify_password, create_access_token, hash_password, get_current_user, UserResponse


router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class RegisterRequest(BaseModel):
    username: str
    password: str
    is_admin: bool = False


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)):
    """Get JWT-токен"""
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(
        data={
            "sub": user.username,
            "is_admin": user.is_admin
        },
        expires_delta=timedelta(hours=1)
    )

    return TokenResponse(access_token=access_token)


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("3/hour")
def register(
        request: Request,
        body: RegisterRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # Требует авторизации
):
    """Register new users (for admins only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can register new users")

    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        is_admin=body.is_admin
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/me", response_model=UserResponse)
@limiter.limit("5/minute")
def get_current_user_info(request: Request, current_user: User = Depends(get_current_user)):
    """Get user info"""
    return current_user
