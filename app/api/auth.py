from datetime import timedelta

import jwt
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, Database
from app.core.config import get_settings
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.modules.users.models import Role, User
from app.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


def serialize_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        roles=[role.name for role in user.roles],
    )


def issue_tokens(user: User) -> TokenResponse:
    settings = get_settings()
    return TokenResponse(
        access_token=create_token(
            user.id, "access", timedelta(minutes=settings.jwt_access_token_minutes)
        ),
        refresh_token=create_token(
            user.id, "refresh", timedelta(days=settings.jwt_refresh_token_days)
        ),
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Database) -> UserResponse:
    if db.scalar(select(User).where(User.email == payload.email.lower())) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    customer_role = db.scalar(select(Role).where(Role.name == "CUSTOMER"))
    if customer_role is None:
        raise HTTPException(status_code=500, detail="Customer role is not configured")
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        roles=[customer_role],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Database) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Database) -> TokenResponse:
    try:
        user_id = decode_token(payload.refresh_token, "refresh")
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from None
    user = db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return issue_tokens(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_: CurrentUser) -> None:
    return None


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> UserResponse:
    return serialize_user(user)
