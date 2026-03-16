import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import cache
from app.main.models import User, Session
from app.main.repositories import UserRepository, SessionRepository
from app.settings import settings

_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


class AuthError(Exception):
    pass


class EmailTakenError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class EmailNotVerifiedError(AuthError):
    pass


class InvalidCodeError(AuthError):
    pass


class InvalidTokenError(AuthError):
    pass


class SessionNotFoundError(AuthError):
    pass


def _generate_code(length: int = 6) -> str:
    return "".join([str(secrets.randbelow(10)) for _ in range(length)])


def _generate_refresh_token() -> str:
    return secrets.token_hex(32)


def _create_access_token(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "uid": str(user_id),
        "exp": now + timedelta(seconds=settings.JWT.ACCESS_TTL_SECONDS),
        "iat": now,
    }
    return jwt.encode(
        payload,
        settings.JWT.ACCESS_SECRET.get_secret_value(),
        algorithm="HS256",
    )


def parse_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(
            token,
            settings.JWT.ACCESS_SECRET.get_secret_value(),
            algorithms=["HS256"],
        )
        return uuid.UUID(payload["uid"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise InvalidTokenError("invalid or expired token") from exc


async def register(session: AsyncSession, email: str, password: str) -> str:
    existing = await UserRepository.find_by_email(session, email)
    if existing:
        raise EmailTakenError("email already registered")

    hashed = _ph.hash(password)
    user = User(email=email, password=hashed)
    await UserRepository.insert(session, user)

    code = _generate_code()
    await cache.set_email_code(email, code, settings.JWT.EMAIL_CODE_TTL_SECONDS)
    return code


async def confirm_email(session: AsyncSession, email: str, code: str) -> None:
    stored = await cache.get_email_code(email)
    if stored is None or stored != code:
        raise InvalidCodeError("invalid or expired code")

    user = await UserRepository.find_by_email(session, email)
    if user is None:
        raise InvalidCodeError("invalid or expired code")

    await UserRepository.mark_verified(session, user.id)
    await cache.delete_email_code(email)


async def login(
    session: AsyncSession, email: str, password: str, user_agent: str, ip: str
) -> dict:
    user = await UserRepository.find_by_email(session, email)
    if user is None:
        raise InvalidCredentialsError("invalid email or password")

    try:
        _ph.verify(user.password, password)
    except VerifyMismatchError:
        raise InvalidCredentialsError("invalid email or password")

    if _ph.check_needs_rehash(user.password):
        user.password = _ph.hash(password)
        await session.flush()

    if not user.is_verified:
        raise EmailNotVerifiedError("email not verified")

    return await _create_session(session, user, user_agent, ip)


async def logout(session: AsyncSession, refresh_token: str) -> None:
    await SessionRepository.delete_by_refresh_token(session, refresh_token)


async def refresh(
    session: AsyncSession, old_refresh_token: str, user_agent: str, ip: str
) -> dict:
    sess = await SessionRepository.find_by_refresh_token(session, old_refresh_token)
    if sess is None:
        raise InvalidTokenError("invalid or expired refresh token")

    if datetime.now(timezone.utc) > sess.expires_at.replace(tzinfo=timezone.utc):
        await SessionRepository.delete_by_refresh_token(session, old_refresh_token)
        raise InvalidTokenError("invalid or expired refresh token")

    user = await UserRepository.find_by_id(session, sess.user_id)
    if user is None:
        raise InvalidTokenError("invalid or expired refresh token")

    new_refresh = _generate_refresh_token()
    new_expires = datetime.now(timezone.utc) + timedelta(seconds=settings.JWT.REFRESH_TTL_SECONDS)

    rows = await SessionRepository.rotate_refresh_token(
        session, old_refresh_token, new_refresh, new_expires
    )
    if rows == 0:
        raise InvalidTokenError("invalid or expired refresh token")

    access_token = _create_access_token(user.id)
    return {
        "access_token": access_token,
        "refresh_token": new_refresh,
        "expires_in": settings.JWT.ACCESS_TTL_SECONDS,
    }


async def get_sessions(session: AsyncSession, user_id: uuid.UUID) -> list[Session]:
    return await SessionRepository.list_active_by_user(session, user_id)


async def revoke_session(
    session: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    rows = await SessionRepository.delete_by_id_and_user(session, session_id, user_id)
    if rows == 0:
        raise SessionNotFoundError("session not found")


async def _create_session(
    session: AsyncSession, user: User, user_agent: str, ip: str
) -> dict:
    access_token = _create_access_token(user.id)
    refresh_token = _generate_refresh_token()

    sess = Session(
        user_id=user.id,
        refresh_token=refresh_token,
        user_agent=user_agent,
        ip=ip,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.JWT.REFRESH_TTL_SECONDS),
    )
    await SessionRepository.insert(session, sess)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": settings.JWT.ACCESS_TTL_SECONDS,
    }
