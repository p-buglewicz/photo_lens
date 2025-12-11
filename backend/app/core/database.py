from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings


def _normalize_database_url(url: str) -> str:
    """Ensure SQLAlchemy URL uses '+' between dialect and driver.

    Some environments may provide URLs like 'postgresql.asyncpg://',
    but SQLAlchemy expects 'postgresql+asyncpg://'. Normalize this
    and leave other URLs unchanged.
    """
    if url.startswith("postgresql.asyncpg://"):
        return url.replace("postgresql.asyncpg://", "postgresql+asyncpg://", 1)
    return url


# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    _normalize_database_url(settings.database_url),
    echo=settings.debug,
    future=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(  # type: ignore[call-overload]
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        yield session
