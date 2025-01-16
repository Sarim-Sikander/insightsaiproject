from contextvars import ContextVar, Token
from typing import Union

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.sql.expression import Delete, Insert, Update

from app.core.config import config

Base = declarative_base()
session_context: ContextVar[str] = ContextVar("session_context")

engine = create_engine(config.DATABASE_URL, pool_recycle=3600)


def get_session_context() -> str:
    return session_context.get()


def set_session_context(session_id: str) -> Token:
    return session_context.set(session_id)


def reset_session_context(context: Token) -> None:
    session_context.reset(context)


class RoutingSession(Session):
    def get_bind(self, mapper=None, clause=None, **kwargs):
        if self._flushing or isinstance(clause, (Update, Delete, Insert)):
            return engine
        return engine


async_session_factory = sessionmaker(
    class_=AsyncSession,
    sync_session_class=RoutingSession,
    expire_on_commit=False,
)

session: Union[AsyncSession, async_scoped_session] = async_scoped_session(
    session_factory=async_session_factory,
    scopefunc=get_session_context,
)


async def get_session():
    try:
        yield session
    finally:
        await session.close()