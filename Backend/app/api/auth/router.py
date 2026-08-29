from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rate_limit import login_rate_limiter, refresh_rate_limiter, register_rate_limiter
from app.models.user import User
from app.schemas.auth import (
    AuthenticatedUser,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthenticatedUser,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(register_rate_limiter)],
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthenticatedUser:
    user = auth_service.register_citizen(db, payload)
    return auth_service.to_authenticated_user(db, user)


@router.post("/login", response_model=LoginResponse, dependencies=[Depends(login_rate_limiter)])
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = auth_service.authenticate(db, payload.email, payload.password)
    return auth_service.build_login_response(db, user)


@router.post("/refresh", response_model=TokenResponse, dependencies=[Depends(refresh_rate_limiter)])
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.refresh_access_token(db, payload.refresh_token)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)) -> dict:
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=AuthenticatedUser)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AuthenticatedUser:
    return auth_service.to_authenticated_user(db, current_user)
