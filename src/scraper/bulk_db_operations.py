#!/usr/bin/env python3
"""
Bulk database operations for efficient batch processing.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .async_db import get_async_session

if TYPE_CHECKING:
    from collections.abc import Callable


class BulkDatabaseOperations:
    """Efficient bulk database operations."""

    def __init__(self, batch_size: int = 100, is_postgres: bool = True):
        """Initialize bulk operations.

        Args:
            batch_size: Number of records per batch.
            is_postgres: Whether the active database is PostgreSQL. When False,
                the SQLite-compatible query path is used. This must be set
                explicitly so dialect errors are never silently swallowed.
        """
        self.batch_size = batch_size
        self.is_postgres = is_postgres

    async def bulk_upsert_categories(
        self, categories: list[dict[str, Any]], session: AsyncSession | None = None
    ) -> list[int]:
        """Bulk upsert categories and return their IDs."""
        if not categories:
            return []

        if session is None:
            async with get_async_session() as session:
                return await self._bulk_upsert_categories_impl(categories, session)
        else:
            return await self._bulk_upsert_categories_impl(categories, session)

    async def _bulk_upsert_categories_impl(
        self, categories: list[dict[str, Any]], session: AsyncSession
    ) -> list[int]:
        """Implementation of bulk category upsert."""
        now = datetime.datetime.now(datetime.timezone.utc)

        category_data = [
            {
                "name": cat["name"],
                "image_url": cat.get("image_url"),
                "created_at": now,
                "updated_at": now,
            }
            for cat in categories
        ]

        if self.is_postgres:
            query = """
            INSERT INTO categories (name, image_url, created_at, updated_at)
            VALUES (:name, :image_url, :created_at, :updated_at)
            ON CONFLICT (name) DO UPDATE SET
                image_url = EXCLUDED.image_url,
                updated_at = EXCLUDED.updated_at
            RETURNING id
            """
            result = await session.execute(text(query), category_data)
            ids = [row[0] for row in result.fetchall()]
            await session.commit()
            return ids
        else:
            query = """
            INSERT OR REPLACE INTO categories (name, image_url, created_at, updated_at)
            VALUES (:name, :image_url, :created_at, :updated_at)
            """
            await session.execute(text(query), category_data)
            await session.commit()

            # Retrieve all IDs in a single query instead of N separate queries
            names = [cat["name"] for cat in categories]
            placeholders = ", ".join(f":name_{i}" for i in range(len(names)))
            id_result = await session.execute(
                text(f"SELECT id, name FROM categories WHERE name IN ({placeholders})"),
                {f"name_{i}": name for i, name in enumerate(names)},
            )
            name_to_id = {row[1]: row[0] for row in id_result.fetchall()}
            return [name_to_id[cat["name"]] for cat in categories if cat["name"] in name_to_id]

    async def bulk_upsert_years(
        self, years: list[dict[str, Any]], session: AsyncSession | None = None
    ) -> list[int]:
        """Bulk upsert years and return their IDs."""
        if not years:
            return []

        if session is None:
            async with get_async_session() as session:
                return await self._bulk_upsert_years_impl(years, session)
        else:
            return await self._bulk_upsert_years_impl(years, session)

    async def _bulk_upsert_years_impl(
        self, years: list[dict[str, Any]], session: AsyncSession
    ) -> list[int]:
        """Implementation of bulk year upsert."""
        now = datetime.datetime.now(datetime.timezone.utc)

        year_data = [
            {
                "category_id": year["category_id"],
                "year": year["year"],
                "created_at": now,
                "updated_at": now,
            }
            for year in years
        ]

        if self.is_postgres:
            query = """
            INSERT INTO years (category_id, year, created_at, updated_at)
            VALUES (:category_id, :year, :created_at, :updated_at)
            ON CONFLICT (category_id, year) DO UPDATE SET
                updated_at = EXCLUDED.updated_at
            RETURNING id
            """
            result = await session.execute(text(query), year_data)
            ids = [row[0] for row in result.fetchall()]
            await session.commit()
            return ids
        else:
            query = """
            INSERT OR REPLACE INTO years (category_id, year, created_at, updated_at)
            VALUES (:category_id, :year, :created_at, :updated_at)
            """
            await session.execute(text(query), year_data)
            await session.commit()

            # Single query for all IDs
            pairs = [(y["category_id"], y["year"]) for y in years]
            conditions = " OR ".join(
                f"(category_id = :cat_{i} AND year = :year_{i})" for i in range(len(pairs))
            )
            params = {}
            for i, (cat_id, yr) in enumerate(pairs):
                params[f"cat_{i}"] = cat_id
                params[f"year_{i}"] = yr
            id_result = await session.execute(
                text(f"SELECT id, category_id, year FROM years WHERE {conditions}"),
                params,
            )
            key_to_id = {(row[1], row[2]): row[0] for row in id_result.fetchall()}
            return [
                key_to_id[(y["category_id"], y["year"])]
                for y in years
                if (y["category_id"], y["year"]) in key_to_id
            ]

    async def bulk_upsert_sets(
        self, sets: list[dict[str, Any]], session: AsyncSession | None = None
    ) -> list[int]:
        """Bulk upsert sets and return their IDs."""
        if not sets:
            return []

        if session is None:
            async with get_async_session() as session:
                return await self._bulk_upsert_sets_impl(sets, session)
        else:
            return await self._bulk_upsert_sets_impl(sets, session)

    async def _bulk_upsert_sets_impl(
        self, sets: list[dict[str, Any]], session: AsyncSession
    ) -> list[int]:
        """Implementation of bulk set upsert."""
        now = datetime.datetime.now(datetime.timezone.utc)

        set_data = [
            {
                "category_id": set_item["category_id"],
                "year_id": set_item["year_id"],
                "set_name": set_item["set_name"],
                "num_sets": set_item.get("num_sets"),
                "total_items": set_item.get("total_items"),
                "created_at": now,
                "updated_at": now,
            }
            for set_item in sets
        ]

        if self.is_postgres:
            query = """
            INSERT INTO sets (category_id, year_id, set_name, num_sets, total_items, created_at, updated_at)
            VALUES (:category_id, :year_id, :set_name, :num_sets, :total_items, :created_at, :updated_at)
            ON CONFLICT (year_id, set_name) DO UPDATE SET
                num_sets = EXCLUDED.num_sets,
                total_items = EXCLUDED.total_items,
                updated_at = EXCLUDED.updated_at
            RETURNING id
            """
            result = await session.execute(text(query), set_data)
            ids = [row[0] for row in result.fetchall()]
            await session.commit()
            return ids
        else:
            query = """
            INSERT OR REPLACE INTO sets (category_id, year_id, set_name, num_sets, total_items, created_at, updated_at)
            VALUES (:category_id, :year_id, :set_name, :num_sets, :total_items, :created_at, :updated_at)
            """
            await session.execute(text(query), set_data)
            await session.commit()

            # Single query for all IDs
            pairs = [(s["year_id"], s["set_name"]) for s in sets]
            conditions = " OR ".join(
                f"(year_id = :yid_{i} AND set_name = :sname_{i})" for i in range(len(pairs))
            )
            params = {}
            for i, (yid, sname) in enumerate(pairs):
                params[f"yid_{i}"] = yid
                params[f"sname_{i}"] = sname
            id_result = await session.execute(
                text(f"SELECT id, year_id, set_name FROM sets WHERE {conditions}"),
                params,
            )
            key_to_id = {(row[1], row[2]): row[0] for row in id_result.fetchall()}
            return [
                key_to_id[(s["year_id"], s["set_name"])]
                for s in sets
                if (s["year_id"], s["set_name"]) in key_to_id
            ]

    async def bulk_upsert_cards(
        self, cards: list[dict[str, Any]], session: AsyncSession | None = None
    ) -> list[int]:
        """Bulk upsert cards and return their IDs."""
        if not cards:
            return []

        if session is None:
            async with get_async_session() as session:
                return await self._bulk_upsert_cards_impl(cards, session)
        else:
            return await self._bulk_upsert_cards_impl(cards, session)

    async def _bulk_upsert_cards_impl(
        self, cards: list[dict[str, Any]], session: AsyncSession
    ) -> list[int]:
        """Implementation of bulk card upsert."""
        now = datetime.datetime.now(datetime.timezone.utc)

        card_data = [
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
            for card in cards
        ]

        if self.is_postgres:
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
            result = await session.execute(text(query), card_data)
            ids = [row[0] for row in result.fetchall()]
            await session.commit()
            return ids
        else:
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

            # Single query for all IDs
            uids = [card["card_uid"] for card in cards]
            placeholders = ", ".join(f":uid_{i}" for i in range(len(uids)))
            id_result = await session.execute(
                text(f"SELECT id, card_uid FROM cards WHERE card_uid IN ({placeholders})"),
                {f"uid_{i}": uid for i, uid in enumerate(uids)},
            )
            uid_to_id = {row[1]: row[0] for row in id_result.fetchall()}
            return [uid_to_id[card["card_uid"]] for card in cards if card["card_uid"] in uid_to_id]

    async def bulk_upsert_population_reports(
        self, reports: list[dict[str, Any]], session: AsyncSession | None = None
    ) -> list[int]:
        """Bulk upsert population reports and return their IDs."""
        if not reports:
            return []

        if session is None:
            async with get_async_session() as session:
                return await self._bulk_upsert_population_reports_impl(reports, session)
        else:
            return await self._bulk_upsert_population_reports_impl(reports, session)

    async def _bulk_upsert_population_reports_impl(
        self, reports: list[dict[str, Any]], session: AsyncSession
    ) -> list[int]:
        """Implementation of bulk population report upsert."""
        now = datetime.datetime.now(datetime.timezone.utc)

        report_data = [
            {
                "card_uid": report["card_uid"],
                "grade_label": report["grade_label"],
                "snapshot_date": report["snapshot_date"],
                "population_count": report["population_count"],
                "total_graded": report.get("total_graded"),
                "created_at": now,
                "updated_at": now,
            }
            for report in reports
        ]

        if self.is_postgres:
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
            result = await session.execute(text(query), report_data)
            ids = [row[0] for row in result.fetchall()]
            await session.commit()
            return ids
        else:
            query = """
            INSERT OR REPLACE INTO population_reports (card_uid, grade_label, snapshot_date,
                                                     population_count, total_graded, created_at, updated_at)
            VALUES (:card_uid, :grade_label, :snapshot_date, :population_count,
                    :total_graded, :created_at, :updated_at)
            """
            await session.execute(text(query), report_data)
            await session.commit()

            # Single query for all IDs
            triples = [(r["card_uid"], r["grade_label"], r["snapshot_date"]) for r in reports]
            conditions = " OR ".join(
                f"(card_uid = :uid_{i} AND grade_label = :gl_{i} AND snapshot_date = :sd_{i})"
                for i in range(len(triples))
            )
            params = {}
            for i, (uid, gl, sd) in enumerate(triples):
                params[f"uid_{i}"] = uid
                params[f"gl_{i}"] = gl
                params[f"sd_{i}"] = sd
            id_result = await session.execute(
                text(
                    f"SELECT id, card_uid, grade_label, snapshot_date FROM population_reports "
                    f"WHERE {conditions}"
                ),
                params,
            )
            key_to_id = {(row[1], row[2], row[3]): row[0] for row in id_result.fetchall()}
            return [
                key_to_id[(r["card_uid"], r["grade_label"], r["snapshot_date"])]
                for r in reports
                if (r["card_uid"], r["grade_label"], r["snapshot_date"]) in key_to_id
            ]

    async def process_batches(
        self,
        items: list[Any],
        process_func: Callable[..., Any],
        session: AsyncSession | None = None,
    ) -> list[Any]:
        """Process items in batches using the specified function."""
        results = []

        for i in range(0, len(items), self.batch_size):
            batch = items[i : i + self.batch_size]
            batch_results = await process_func(batch, session)
            results.extend(batch_results)

        return results
