from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.settings import settings

engine = create_async_engine(settings.DATABASE.async_url, echo=settings.DATABASE.LOG_DATABASE)
session_local = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    @classmethod
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


async def get_db_read():
    async with session_local() as session:
        yield session


async def get_db_write():
    async with session_local.begin() as session:
        yield session
