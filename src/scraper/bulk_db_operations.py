#!/usr/bin/env python3
"""
Bulk database operations for efficient batch processing.
"""

import asyncio
import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .async_db import get_async_session


class BulkDatabaseOperations:
    """Efficient bulk database operations."""

    def __init__(self, batch_size: int = 100):
        """Initialize bulk operations."""
        self.batch_size = batch_size

    async def bulk_upsert_categories(
        self, categories: List[Dict[str, Any]], session: Optional[AsyncSession] = None
    ) -> List[int]:
        """Bulk upsert categories and return their IDs."""
        if not categories:
            return []

        if session is None:
            async with get_async_session() as session:
                return await self._bulk_upsert_categories_impl(categories, session)
        else:
            return await self._bulk_upsert_categories_impl(categories, session)

    async def _bulk_upsert_categories_impl(
        self, categories: List[Dict[str, Any]], session: AsyncSession
    ) -> List[int]:
        """Implementation of bulk category upsert."""
        now = datetime.datetime.now(datetime.timezone.utc)

        # Prepare data for bulk insert
        category_data = []
        for cat in categories:
            category_data.append(
                {
                    "name": cat["name"],
                    "image_url": cat.get("image_url"),
                    "created_at": now,
                    "updated_at": now,
                }
            )

        # Use PostgreSQL ON CONFLICT or SQLite INSERT OR REPLACE
        query = """
        INSERT INTO categories (name, image_url, created_at, updated_at)
        VALUES (:name, :image_url, :created_at, :updated_at)
        ON CONFLICT (name) DO UPDATE SET
            image_url = EXCLUDED.image_url,
            updated_at = EXCLUDED.updated_at
        RETURNING id
        """

        # For SQLite compatibility, we'll use a different approach
        # This is a simplified version - in production you'd want proper dialect detection
        try:
            result = await session.execute(text(query), category_data)
            ids = [row[0] for row in result.fetchall()]
            await session.commit()
            return ids
        except Exception:
            # Fallback to SQLite syntax
            query = """
            INSERT OR REPLACE INTO categories (name, image_url, created_at, updated_at)
            VALUES (:name, :image_url, :created_at, :updated_at)
            """
            await session.execute(text(query), category_data)
            await session.commit()

            # Get IDs separately for SQLite
            id_query = "SELECT id FROM categories WHERE name = :name"
            ids = []
            for cat in categories:
                result = await session.execute(text(id_query), {"name": cat["name"]})
                row = result.fetchone()
                if row:
                    ids.append(row[0])
            return ids

    async def bulk_upsert_years(
        self, years: List[Dict[str, Any]], session: Optional[AsyncSession] = None
    ) -> List[int]:
        """Bulk upsert years and return their IDs."""
        if not years:
            return []

        if session is None:
            async with get_async_session() as session:
                return await self._bulk_upsert_years_impl(years, session)
        else:
            return await self._bulk_upsert_years_impl(years, session)

    async def _bulk_upsert_years_impl(
        self, years: List[Dict[str, Any]], session: AsyncSession
    ) -> List[int]:
        """Implementation of bulk year upsert."""
        now = datetime.datetime.now(datetime.timezone.utc)

        # Prepare data for bulk insert
        year_data = []
        for year in years:
            year_data.append(
                {
                    "category_id": year["category_id"],
                    "year": year["year"],
                    "created_at": now,
                    "updated_at": now,
                }
            )

        query = """
        INSERT INTO years (category_id, year, created_at, updated_at)
        VALUES (:category_id, :year, :created_at, :updated_at)
        ON CONFLICT (category_id, year) DO UPDATE SET
            updated_at = EXCLUDED.updated_at
        RETURNING id
        """

        try:
            result = await session.execute(text(query), year_data)
            ids = [row[0] for row in result.fetchall()]
            await session.commit()
            return ids
        except Exception:
            # SQLite fallback
            query = """
            INSERT OR REPLACE INTO years (category_id, year, created_at, updated_at)
            VALUES (:category_id, :year, :created_at, :updated_at)
            """
            await session.execute(text(query), year_data)
            await session.commit()

            # Get IDs separately
            id_query = (
                "SELECT id FROM years WHERE category_id = :category_id AND year = :year"
            )
            ids = []
            for year in years:
                result = await session.execute(
                    text(id_query),
                    {"category_id": year["category_id"], "year": year["year"]},
                )
                row = result.fetchone()
                if row:
                    ids.append(row[0])
            return ids

    async def bulk_upsert_sets(
        self, sets: List[Dict[str, Any]], session: Optional[AsyncSession] = None
    ) -> List[int]:
        """Bulk upsert sets and return their IDs."""
        if not sets:
            return []

        if session is None:
            async with get_async_session() as session:
                return await self._bulk_upsert_sets_impl(sets, session)
        else:
            return await self._bulk_upsert_sets_impl(sets, session)

    async def _bulk_upsert_sets_impl(
        self, sets: List[Dict[str, Any]], session: AsyncSession
    ) -> List[int]:
        """Implementation of bulk set upsert."""
        now = datetime.datetime.now(datetime.timezone.utc)

        # Prepare data for bulk insert
        set_data = []
        for set_item in sets:
            set_data.append(
                {
                    "category_id": set_item["category_id"],
                    "year_id": set_item["year_id"],
                    "set_name": set_item["set_name"],
                    "num_sets": set_item.get("num_sets"),
                    "total_items": set_item.get("total_items"),
                    "created_at": now,
                    "updated_at": now,
                }
            )

        query = """
        INSERT INTO sets (category_id, year_id, set_name, num_sets, total_items, created_at, updated_at)
        VALUES (:category_id, :year_id, :set_name, :num_sets, :total_items, :created_at, :updated_at)
        ON CONFLICT (year_id, set_name) DO UPDATE SET
            num_sets = EXCLUDED.num_sets,
            total_items = EXCLUDED.total_items,
            updated_at = EXCLUDED.updated_at
        RETURNING id
        """

        try:
            result = await session.execute(text(query), set_data)
            ids = [row[0] for row in result.fetchall()]
            await session.commit()
            return ids
        except Exception:
            # SQLite fallback
            query = """
            INSERT OR REPLACE INTO sets (category_id, year_id, set_name, num_sets, total_items, created_at, updated_at)
            VALUES (:category_id, :year_id, :set_name, :num_sets, :total_items, :created_at, :updated_at)
            """
            await session.execute(text(query), set_data)
            await session.commit()

            # Get IDs separately
            id_query = (
                "SELECT id FROM sets WHERE year_id = :year_id AND set_name = :set_name"
            )
            ids = []
            for set_item in sets:
                result = await session.execute(
                    text(id_query),
                    {"year_id": set_item["year_id"], "set_name": set_item["set_name"]},
                )
                row = result.fetchone()
                if row:
                    ids.append(row[0])
            return ids

    async def bulk_upsert_cards(
        self, cards: List[Dict[str, Any]], session: Optional[AsyncSession] = None
    ) -> List[int]:
        """Bulk upsert cards and return their IDs."""
        if not cards:
            return []

        if session is None:
            async with get_async_session() as session:
                return await self._bulk_upsert_cards_impl(cards, session)
        else:
            return await self._bulk_upsert_cards_impl(cards, session)

    async def _bulk_upsert_cards_impl(
        self, cards: List[Dict[str, Any]], session: AsyncSession
    ) -> List[int]:
        """Implementation of bulk card upsert."""
        now = datetime.datetime.now(datetime.timezone.utc)

        # Prepare data for bulk insert
        card_data = []
        for card in cards:
            card_data.append(
                {
                    "card_uid": card["card_uid"],
                    "category_id": card["category_id"],
                    "year_id": card["year_id"],
                    "set_id": card["set_id"],
                    "card_number": card.get("card_number"),
                    "player": card.get("player"),
                    "detail_url": card.get("detail_url"),
                    "image_url": card.get("image_url"),
                    "subset_name": card.get("subset_name"),
                    "variation": card.get("variation"),
                    "cert_number": card.get("cert_number"),
                    "created_at": now,
                    "updated_at": now,
                }
            )

        query = """
        INSERT INTO cards (card_uid, category_id, year_id, set_id, card_number, player,
                          detail_url, image_url, subset_name, variation, cert_number,
                          created_at, updated_at)
        VALUES (:card_uid, :category_id, :year_id, :set_id, :card_number, :player,
                :detail_url, :image_url, :subset_name, :variation, :cert_number,
                :created_at, :updated_at)
        ON CONFLICT (card_uid) DO UPDATE SET
            category_id = EXCLUDED.category_id,
            year_id = EXCLUDED.year_id,
            set_id = EXCLUDED.set_id,
            card_number = EXCLUDED.card_number,
            player = EXCLUDED.player,
            detail_url = EXCLUDED.detail_url,
            image_url = EXCLUDED.image_url,
            subset_name = EXCLUDED.subset_name,
            variation = EXCLUDED.variation,
            cert_number = EXCLUDED.cert_number,
            updated_at = EXCLUDED.updated_at
        RETURNING id
        """

        try:
            result = await session.execute(text(query), card_data)
            ids = [row[0] for row in result.fetchall()]
            await session.commit()
            return ids
        except Exception:
            # SQLite fallback
            query = """
            INSERT OR REPLACE INTO cards (card_uid, category_id, year_id, set_id, card_number, player,
                                        detail_url, image_url, subset_name, variation, cert_number,
                                        created_at, updated_at)
            VALUES (:card_uid, :category_id, :year_id, :set_id, :card_number, :player,
                    :detail_url, :image_url, :subset_name, :variation, :cert_number,
                    :created_at, :updated_at)
            """
            await session.execute(text(query), card_data)
            await session.commit()

            # Get IDs separately
            id_query = "SELECT id FROM cards WHERE card_uid = :card_uid"
            ids = []
            for card in cards:
                result = await session.execute(
                    text(id_query), {"card_uid": card["card_uid"]}
                )
                row = result.fetchone()
                if row:
                    ids.append(row[0])
            return ids

    async def bulk_upsert_population_reports(
        self, reports: List[Dict[str, Any]], session: Optional[AsyncSession] = None
    ) -> List[int]:
        """Bulk upsert population reports and return their IDs."""
        if not reports:
            return []

        if session is None:
            async with get_async_session() as session:
                return await self._bulk_upsert_population_reports_impl(reports, session)
        else:
            return await self._bulk_upsert_population_reports_impl(reports, session)

    async def _bulk_upsert_population_reports_impl(
        self, reports: List[Dict[str, Any]], session: AsyncSession
    ) -> List[int]:
        """Implementation of bulk population report upsert."""
        now = datetime.datetime.now(datetime.timezone.utc)

        # Prepare data for bulk insert
        report_data = []
        for report in reports:
            report_data.append(
                {
                    "card_uid": report["card_uid"],
                    "grade_label": report["grade_label"],
                    "snapshot_date": report["snapshot_date"],
                    "population_count": report["population_count"],
                    "total_graded": report.get("total_graded"),
                    "created_at": now,
                    "updated_at": now,
                }
            )

        query = """
        INSERT INTO population_reports (card_uid, grade_label, snapshot_date, population_count,
                                      total_graded, created_at, updated_at)
        VALUES (:card_uid, :grade_label, :snapshot_date, :population_count,
                :total_graded, :created_at, :updated_at)
        ON CONFLICT (card_uid, grade_label, snapshot_date) DO UPDATE SET
            population_count = EXCLUDED.population_count,
            total_graded = EXCLUDED.total_graded,
            updated_at = EXCLUDED.updated_at
        RETURNING id
        """

        try:
            result = await session.execute(text(query), report_data)
            ids = [row[0] for row in result.fetchall()]
            await session.commit()
            return ids
        except Exception:
            # SQLite fallback
            query = """
            INSERT OR REPLACE INTO population_reports (card_uid, grade_label, snapshot_date,
                                                     population_count, total_graded, created_at, updated_at)
            VALUES (:card_uid, :grade_label, :snapshot_date, :population_count,
                    :total_graded, :created_at, :updated_at)
            """
            await session.execute(text(query), report_data)
            await session.commit()

            # Get IDs separately
            id_query = """
            SELECT id FROM population_reports
            WHERE card_uid = :card_uid AND grade_label = :grade_label AND snapshot_date = :snapshot_date
            """
            ids = []
            for report in reports:
                result = await session.execute(
                    text(id_query),
                    {
                        "card_uid": report["card_uid"],
                        "grade_label": report["grade_label"],
                        "snapshot_date": report["snapshot_date"],
                    },
                )
                row = result.fetchone()
                if row:
                    ids.append(row[0])
            return ids

    async def process_batches(
        self,
        items: List[Any],
        process_func: callable,
        session: Optional[AsyncSession] = None,
    ) -> List[Any]:
        """Process items in batches using the specified function."""
        results = []

        for i in range(0, len(items), self.batch_size):
            batch = items[i : i + self.batch_size]
            batch_results = await process_func(batch, session)
            results.extend(batch_results)

        return results
