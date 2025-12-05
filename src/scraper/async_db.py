#!/usr/bin/env python3
"""
Async database connection pool and operations for the scraping pipeline.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import os
import sys
from typing import Any

# Handle ExceptionGroup for Python < 3.11
if sys.version_info < (3, 11):
    try:
        from exceptiongroup import ExceptionGroup
    except ImportError:
        # Fallback: create a simple ExceptionGroup-like class
        class ExceptionGroup(Exception):
            def __init__(self, message: str, exceptions: list[Exception]):
                super().__init__(message)
                self.exceptions = exceptions

    # Provide a BaseExceptionGroup-compatible name for older runtimes
    BaseExceptionGroup = ExceptionGroup
else:
    from builtins import BaseExceptionGroup

    ExceptionGroup = BaseExceptionGroup

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Load environment variables
project_root = os.path.dirname(os.path.dirname(__file__))
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path=dotenv_path)

# Database configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_DB = os.getenv("POSTGRES_DB", "tag_scraper")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")


class AsyncDatabasePool:
    """Async database connection pool with PostgreSQL and SQLite support."""

    def __init__(
        self,
        pool_size: int = 20,
        max_overflow: int = 30,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        enable_postgres: bool = True,
    ):
        """
        Initialize async database pool.

        Args:
            pool_size: Base pool size
            max_overflow: Maximum overflow connections
            pool_timeout: Pool timeout in seconds
            pool_recycle: Connection recycle time in seconds
            enable_postgres: Whether to try PostgreSQL first
        """
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.enable_postgres = enable_postgres

        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self._is_postgres = False

    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        if self.enable_postgres:
            try:
                await self._init_postgres()
                self._is_postgres = True
                print("✅ PostgreSQL async connection pool initialized")
            except Exception as e:
                print(f"⚠️  PostgreSQL connection failed: {e}")
                print("🔄 Falling back to SQLite")
                await self._init_sqlite()
                self._is_postgres = False
        else:
            await self._init_sqlite()
            self._is_postgres = False

    async def _init_postgres(self) -> None:
        """Initialize PostgreSQL connection pool."""
        if POSTGRES_PASSWORD:
            dsn = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        else:
            dsn = f"postgresql+asyncpg://{POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

        self.engine = create_async_engine(
            dsn,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            echo=False,
            future=True,
        )

        # Test connection
        async with self.engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def _init_sqlite(self) -> None:
        """Initialize SQLite connection pool."""
        sqlite_path = os.path.join(project_root, "tag_scraper_local.db")
        dsn = f"sqlite+aiosqlite:///{sqlite_path}"

        self.engine = create_async_engine(
            dsn,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            echo=False,
            future=True,
        )

        # Test connection
        async with self.engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        print(f"✅ SQLite async connection pool initialized at: {sqlite_path}")

    @asynccontextmanager
    async def get_session(self):
        """Get async database session."""
        if not self.session_factory:
            raise RuntimeError("Database pool not initialized")

        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Close the database pool."""
        if self.engine:
            await self.engine.dispose()

    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL."""
        return self._is_postgres


class AsyncBulkOperations:
    """Async bulk database operations for efficient batch processing."""

    def __init__(
        self,
        db_pool: AsyncDatabasePool,
        batch_size: int = 100,
        max_concurrent_batches: int = 5,
    ):
        """
        Initialize bulk operations.

        Args:
            db_pool: Database pool instance
            batch_size: Size of each batch for processing
            max_concurrent_batches: Maximum concurrent batch operations
        """
        self.db_pool = db_pool
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches

    async def _process_batches_concurrently(
        self,
        records: list[dict[str, Any]],
        table_name: str,
        unique_keys: list[str],
    ) -> None:
        """
        Process records in batches concurrently using TaskGroup.

        Args:
            records: Records to process
            table_name: Target table name
            unique_keys: Unique key columns for conflict resolution
        """
        if not records:
            return

        # Split into batches
        batches = [
            records[i : i + self.batch_size]
            for i in range(0, len(records), self.batch_size)
        ]

        # Use semaphore to limit concurrent batches
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)

        async def process_batch(batch: list[dict[str, Any]]) -> None:
            async with semaphore:
                async with self.db_pool.get_session() as session:
                    if self.db_pool.is_postgres:
                        await self._bulk_upsert_postgres(
                            session, table_name, batch, unique_keys
                        )
                    else:
                        await self._bulk_upsert_sqlite(
                            session, table_name, batch, unique_keys
                        )

        # Process batches concurrently using TaskGroup
        if len(batches) == 1:
            # Single batch, no need for concurrency
            await process_batch(batches[0])
        else:
            try:
                async with asyncio.TaskGroup() as tg:
                    for batch in batches:
                        tg.create_task(process_batch(batch))
            except ExceptionGroup as eg:
                # Log exceptions but don't fail completely (Python 3.11+)
                for exc in eg.exceptions:
                    print(f"⚠️  Batch processing error: {exc}")
            except Exception as e:
                # Fallback for Python < 3.11 or non-ExceptionGroup exceptions
                print(f"⚠️  Batch processing error: {e}")

    async def bulk_upsert_categories(self, categories: list[dict[str, Any]]) -> None:
        """Bulk upsert categories."""
        if not categories:
            return

        async with self.db_pool.get_session() as session:
            if self.db_pool.is_postgres:
                await self._bulk_upsert_postgres(
                    session, "categories", categories, ["name"]
                )
            else:
                await self._bulk_upsert_sqlite(
                    session, "categories", categories, ["name"]
                )

    async def bulk_upsert_years(self, years: list[dict[str, Any]]) -> None:
        """Bulk upsert years."""
        if not years:
            return

        async with self.db_pool.get_session() as session:
            if self.db_pool.is_postgres:
                await self._bulk_upsert_postgres(
                    session, "years", years, ["category_id", "year"]
                )
            else:
                await self._bulk_upsert_sqlite(
                    session, "years", years, ["category_id", "year"]
                )

    async def bulk_upsert_sets(self, sets: list[dict[str, Any]]) -> None:
        """Bulk upsert sets."""
        if not sets:
            return

        async with self.db_pool.get_session() as session:
            if self.db_pool.is_postgres:
                await self._bulk_upsert_postgres(
                    session, "sets", sets, ["year_id", "set_name"]
                )
            else:
                await self._bulk_upsert_sqlite(
                    session, "sets", sets, ["year_id", "set_name"]
                )

    async def bulk_upsert_cards(self, cards: list[dict[str, Any]]) -> None:
        """Bulk upsert cards with concurrent batch processing for large datasets."""
        if not cards:
            return

        # Use concurrent batch processing for large datasets
        if len(cards) > self.batch_size * 2:
            await self._process_batches_concurrently(cards, "cards", ["card_uid"])
        else:
            async with self.db_pool.get_session() as session:
                if self.db_pool.is_postgres:
                    await self._bulk_upsert_postgres(
                        session, "cards", cards, ["card_uid"]
                    )
                else:
                    await self._bulk_upsert_sqlite(
                        session, "cards", cards, ["card_uid"]
                    )

    async def bulk_upsert_population_reports(
        self, reports: list[dict[str, Any]]
    ) -> None:
        """Bulk upsert population reports."""
        if not reports:
            return

        async with self.db_pool.get_session() as session:
            if self.db_pool.is_postgres:
                await self._bulk_upsert_postgres(
                    session,
                    "population_reports",
                    reports,
                    ["card_uid", "grade_label", "snapshot_date"],
                )
            else:
                await self._bulk_upsert_sqlite(
                    session,
                    "population_reports",
                    reports,
                    ["card_uid", "grade_label", "snapshot_date"],
                )

    async def _bulk_upsert_postgres(
        self,
        session: AsyncSession,
        table_name: str,
        records: list[dict[str, Any]],
        unique_keys: list[str],
    ) -> None:
        """Bulk upsert for PostgreSQL using ON CONFLICT."""
        if not records:
            return

        # Build column names from first record
        columns = list(records[0].keys())

        # Build conflict resolution
        conflict_clause = f"ON CONFLICT ({', '.join(unique_keys)}) DO UPDATE SET "
        update_clauses = []

        for col in columns:
            if col not in unique_keys:
                update_clauses.append(f"{col} = EXCLUDED.{col}")

        if update_clauses:
            conflict_clause += ", ".join(update_clauses)
        else:
            conflict_clause += "updated_at = EXCLUDED.updated_at"

        # Build VALUES clause with proper placeholders for each row
        num_cols = len(columns)
        param_counter = 1
        row_placeholders = []
        for _ in records:
            row_placeholder = (
                "(" + ", ".join(f"${param_counter + j}" for j in range(num_cols)) + ")"
            )
            row_placeholders.append(row_placeholder)
            param_counter += num_cols
        values_clauses = ", ".join(row_placeholders)

        # Build final query
        query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES {values_clauses}
        {conflict_clause}
        """

        # Prepare data as flat list for positional parameters
        values = []
        for record in records:
            values.extend(record[col] for col in columns)

        # Execute bulk insert
        await session.execute(text(query), tuple(values))
        await session.commit()

    async def _bulk_upsert_sqlite(
        self,
        session: AsyncSession,
        table_name: str,
        records: list[dict[str, Any]],
        unique_keys: list[str],
    ) -> None:
        """Bulk upsert for SQLite using INSERT OR REPLACE."""
        if not records:
            return

        # Build column names from first record
        columns = list(records[0].keys())
        placeholders = [f":{col}" for col in columns]

        # Build query
        query = f"""
        INSERT OR REPLACE INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        """

        # Execute bulk insert
        await session.execute(text(query), records)
        await session.commit()


# Global database pool instance
_db_pool: AsyncDatabasePool | None = None


async def get_db_pool() -> AsyncDatabasePool:
    """Get global database pool instance."""
    global _db_pool
    if _db_pool is None:
        _db_pool = AsyncDatabasePool()
        await _db_pool.initialize()
    return _db_pool


async def close_db_pool() -> None:
    """Close global database pool."""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        _db_pool = None


@asynccontextmanager
async def get_async_session():
    """Get async database session from global pool."""
    db_pool = await get_db_pool()
    async with db_pool.get_session() as session:
        yield session


async def get_bulk_operations() -> AsyncBulkOperations:
    """Get bulk operations instance."""
    db_pool = await get_db_pool()
    return AsyncBulkOperations(db_pool)
