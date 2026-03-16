import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_write, get_db_read
from app.main.dependencies import get_current_user_id
from app.main.schema import (
    ConfirmEmailRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    SessionListResponse,
    SessionView,
    TokenResponse,
)
from app.main.service import (
    EmailNotVerifiedError,
    EmailTakenError,
    InvalidCodeError,
    InvalidCredentialsError,
    InvalidTokenError,
    SessionNotFoundError,
    confirm_email,
    get_sessions,
    login,
    logout,
    refresh,
    register,
    revoke_session,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_db_write),
):
    try:
        code = await registeчr(session, body.email, body.password)
    except EmailTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email already registered")

    return RegisterResponse(
        message="registration successful, check your email",
        confirm_code=code,  # убрать в production
    )


@router.post("/register/confirm", response_model=MessageResponse)
async def confirm_email_endpoint(
    body: ConfirmEmailRequest,
    session: AsyncSession = Depends(get_db_write),
):
    try:
        await confirm_email(session, body.email, body.code)
    except InvalidCodeError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid or expired code")

    return MessageResponse(message="email confirmed")


@router.post("/login", response_model=TokenResponse)
async def login_user(
    body: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_write),
):
    user_agent = request.headers.get("User-Agent", "")
    ip = request.client.host if request.client else ""

    try:
        tokens = await login(session, body.email, body.password, user_agent, ip)
    except InvalidCredentialsError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid email or password")
    except EmailNotVerifiedError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="email not verified")

    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    body: RefreshRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_write),
):
    user_agent = request.headers.get("User-Agent", "")
    ip = request.client.host if request.client else ""

    try:
        tokens = await refresh(session, body.refresh_token, user_agent, ip)
    except InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid or expired refresh token")

    return TokenResponse(**tokens)


@router.post("/logout", response_model=MessageResponse)
async def logout_user(
    body: LogoutRequest,
    session: AsyncSession = Depends(get_db_write),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    await logout(session, body.refresh_token)
    return MessageResponse(message="logged out")


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    session: AsyncSession = Depends(get_db_read),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    sessions = await get_sessions(session, user_id)
    return SessionListResponse(
        sessions=[SessionView.model_validate(s) for s in sessions]
    )


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def revoke_session_endpoint(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_write),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    try:
        await revoke_session(session, session_id, user_id)
    except SessionNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found")

    return MessageResponse(message="session revoked")
