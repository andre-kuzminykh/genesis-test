"""
Database connection management.

## Traceability
Feature: F001-F009 — All features
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from core.config import config


class DatabaseConnect:
    def __init__(self):
        self._engine = None
        self._session_factory = None

    def init(self, database_url: str | None = None):
        url = database_url or config.database_url
        self._engine = create_async_engine(url, echo=False)
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

    @property
    def engine(self):
        return self._engine

    async def get_session(self):
        if self._session_factory is None:
            self.init()
        async with self._session_factory() as session:
            yield session


db_connect = DatabaseConnect()
