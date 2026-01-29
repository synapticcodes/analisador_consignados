"""
Database configuration and session management.
Uses SQLAlchemy 2.0 async engine.
"""

from typing import AsyncGenerator

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ==============================================
# Naming Convention for Constraints
# ==============================================
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


# ==============================================
# Base Class for all Models
# ==============================================
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    metadata = metadata

    # Permite repr() automático para debugging
    def __repr__(self) -> str:
        columns = ", ".join(
            f"{k}={repr(v)}" for k, v in self.__dict__.items() if not k.startswith("_")
        )
        return f"<{self.__class__.__name__}({columns})>"


# ==============================================
# Async Engine
# ==============================================
engine: AsyncEngine = create_async_engine(
    str(settings.database_url),
    echo=settings.debug,  # Log SQL queries in debug mode
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,  # Verify connections before using
)

# ==============================================
# Session Factory
# ==============================================
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Permite acessar objetos fora da sessão
    autoflush=False,  # Controle manual de flush
    autocommit=False,
)


# ==============================================
# Dependency for FastAPI
# ==============================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency que fornece uma sessão de banco de dados.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ==============================================
# Database Utilities
# ==============================================
async def init_db() -> None:
    """
    Inicializa o banco de dados criando todas as tabelas.
    ATENÇÃO: Use apenas em desenvolvimento! Em produção, use Alembic.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Fecha o engine do banco de dados."""
    await engine.dispose()


async def check_db_connection() -> bool:
    """
    Verifica se a conexão com o banco está funcionando.
    Útil para health checks.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
