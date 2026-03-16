from typing import Any, List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    model = None

    @classmethod
    async def get_by(cls, session: AsyncSession, **filter_by) -> Optional[Any]:
        query = select(cls.model).filter_by(**filter_by)
        result = await session.execute(query)
        return result.scalars().first()

    @classmethod
    async def find_all(cls, session: AsyncSession, **filter_by) -> List[Any]:
        query = select(cls.model).filter_by(**filter_by)
        result = await session.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def insert(cls, session: AsyncSession, obj: Any) -> None:
        session.add(obj)
        await session.flush()

    @classmethod
    async def update_by(cls, session: AsyncSession, filter_by: dict, **values) -> int:
        query = (
            sa_update(cls.model)
            .where(*[getattr(cls.model, k) == v for k, v in filter_by.items()])
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        result = await session.execute(query)
        await session.flush()
        return result.rowcount

    @classmethod
    async def delete_by(cls, session: AsyncSession, **filter_by) -> int:
        query = delete(cls.model).filter_by(**filter_by)
        result = await session.execute(query)
        await session.flush()
        return result.rowcount

    @classmethod
    async def count(cls, session: AsyncSession, **filter_by) -> int:
        query = select(func.count()).select_from(cls.model).filter_by(**filter_by)
        result = await session.execute(query)
        return result.scalar()
