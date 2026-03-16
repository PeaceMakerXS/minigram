import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository_base import BaseRepository
from app.main.models import User, Session


class UserRepository(BaseRepository):
    model = User

    @classmethod
    async def find_by_email(cls, session: AsyncSession, email: str) -> Optional[User]:
        return await cls.get_by(session, email=email)

    @classmethod
    async def find_by_id(cls, session: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        return await cls.get_by(session, id=user_id)

    @classmethod
    async def mark_verified(cls, session: AsyncSession, user_id: uuid.UUID) -> None:
        await cls.update_by(session, {"id": user_id}, is_verified=True)


class SessionRepository(BaseRepository):
    model = Session

    @classmethod
    async def find_by_refresh_token(cls, session: AsyncSession, token: str) -> Optional[Session]:
        return await cls.get_by(session, refresh_token=token)

    @classmethod
    async def list_active_by_user(
        cls, session: AsyncSession, user_id: uuid.UUID
    ) -> List[Session]:
        now = datetime.now(timezone.utc)
        query = (
            select(cls.model)
            .where(cls.model.user_id == user_id, cls.model.expires_at > now)
            .order_by(cls.model.created_at.desc())
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def delete_by_refresh_token(cls, session: AsyncSession, token: str) -> int:
        return await cls.delete_by(session, refresh_token=token)

    @classmethod
    async def delete_by_id_and_user(
        cls, session: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> int:
        query = (
            delete(cls.model)
            .where(cls.model.id == session_id, cls.model.user_id == user_id)
        )
        result = await session.execute(query)
        await session.flush()
        return result.rowcount

    @classmethod
    async def rotate_refresh_token(
        cls,
        session: AsyncSession,
        old_token: str,
        new_token: str,
        new_expires_at: datetime,
    ) -> int:
        query = (
            update(cls.model)
            .where(cls.model.refresh_token == old_token)
            .values(refresh_token=new_token, expires_at=new_expires_at)
            .execution_options(synchronize_session="fetch")
        )
        result = await session.execute(query)
        await session.flush()
        return result.rowcount
