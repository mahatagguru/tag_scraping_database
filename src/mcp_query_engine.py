#!/usr/bin/env python3
"""
Query engine for TAG Grading population data.

All database diagnostic output is sent to stderr so it does not pollute
the MCP stdio transport, which communicates over stdout.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

_src_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_src_dir)

load_dotenv(os.path.join(_project_root, ".env"))


def _build_db_url() -> str:
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")
    db = os.getenv("POSTGRES_DB", "tag_scraper")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return f"postgresql://{user}@{host}:{port}/{db}"


def _create_engine():
    db_url = _build_db_url()
    try:
        eng = create_engine(db_url, echo=False, future=True, pool_pre_ping=True)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[mcp_query_engine] PostgreSQL connection OK", file=sys.stderr)
        return eng, "postgresql"
    except Exception as exc:
        print(
            f"[mcp_query_engine] PostgreSQL unavailable ({exc}), using SQLite fallback",
            file=sys.stderr,
        )
        sqlite_path = os.path.join(_project_root, "tag_scraper_local.db")
        eng = create_engine(
            f"sqlite:///{sqlite_path}", echo=False, future=True, pool_pre_ping=True
        )
        print(f"[mcp_query_engine] SQLite database: {sqlite_path}", file=sys.stderr)
        return eng, "sqlite"


_engine, _db_dialect = _create_engine()
_SessionFactory = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


@contextmanager
def _session():
    """Yield a read-only SQLAlchemy session."""
    sess: Session = _SessionFactory()
    try:
        yield sess
    finally:
        sess.close()


def _row_to_dict(row) -> dict[str, Any]:
    """Convert a SQLAlchemy Row to a plain dict, serialising non-JSON types."""
    d = dict(row._mapping)
    for k, v in d.items():
        if hasattr(v, "isoformat"):  # datetime / date
            d[k] = v.isoformat()
    return d


# ---------------------------------------------------------------------------
# 1. list_sports
# ---------------------------------------------------------------------------


def list_sports() -> list[dict[str, Any]]:
    """
    Return all sports/categories with their year and set counts.

    Returns a list of dicts with keys:
        sport, year_count, set_count, last_discovered
    """
    sql = text(
        """
        SELECT
            yi.sport,
            COUNT(DISTINCT yi.year)                        AS year_count,
            COUNT(DISTINCT spy.set_title)                  AS set_count,
            MAX(yi.discovered_at)                          AS last_discovered
        FROM years_index yi
        LEFT JOIN sets_per_year spy
               ON spy.sport = yi.sport
              AND spy.is_active = true
        WHERE yi.is_active = true
        GROUP BY yi.sport
        ORDER BY yi.sport
        """
    )
    with _session() as sess:
        rows = sess.execute(sql).fetchall()
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# 2. list_years
# ---------------------------------------------------------------------------


def list_years(sport: str) -> list[dict[str, Any]]:
    """
    Return all years available for a given sport.

    Returns a list of dicts with keys:
        year, set_count, year_url
    """
    sql = text(
        """
        SELECT
            yi.year,
            yi.year_url,
            COUNT(DISTINCT spy.set_title) AS set_count
        FROM years_index yi
        LEFT JOIN sets_per_year spy
               ON spy.sport = yi.sport
              AND spy.year  = yi.year
              AND spy.is_active = true
        WHERE yi.sport = :sport
          AND yi.is_active = true
        GROUP BY yi.year, yi.year_url
        ORDER BY yi.year DESC
        """
    )
    with _session() as sess:
        rows = sess.execute(sql, {"sport": sport}).fetchall()
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# 3. list_sets
# ---------------------------------------------------------------------------


def list_sets(sport: str, year: str) -> list[dict[str, Any]]:
    """
    Return all sets for a given sport and year.

    Returns a list of dicts with keys:
        set_title, card_count, metrics
    """
    sql = text(
        """
        SELECT
            spy.set_title,
            spy.metrics,
            COUNT(DISTINCT cps.card_name) AS card_count
        FROM sets_per_year spy
        LEFT JOIN cards_per_set cps
               ON cps.sport     = spy.sport
              AND cps.year      = spy.year
              AND cps.set_title = spy.set_title
              AND cps.is_active = true
        WHERE spy.sport = :sport
          AND spy.year  = :year
          AND spy.is_active = true
        GROUP BY spy.set_title, spy.metrics
        ORDER BY spy.set_title
        """
    )
    with _session() as sess:
        rows = sess.execute(sql, {"sport": sport, "year": year}).fetchall()
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# 4. search_cards
# ---------------------------------------------------------------------------


def search_cards(
    query: str,
    sport: str | None = None,
    year: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Search cards by name across the database.

    Returns a list of dicts with keys:
        sport, year, set_title, card_name, cert_count
    Ordered by cert_count descending.
    """
    pattern = f"%{query.lower()}%"
    filters = "LOWER(cgr.card_name) LIKE :pattern"
    params: dict[str, Any] = {"pattern": pattern, "limit": limit}

    if sport:
        filters += " AND cgr.sport = :sport"
        params["sport"] = sport
    if year:
        filters += " AND cgr.year = :year"
        params["year"] = year

    sql = text(
        f"""
        SELECT
            cgr.sport,
            cgr.year,
            cgr.set_title,
            cgr.card_name,
            COUNT(cgr.cert_number) AS cert_count
        FROM card_grade_rows cgr
        WHERE {filters}
          AND cgr.is_active = true
        GROUP BY cgr.sport, cgr.year, cgr.set_title, cgr.card_name
        ORDER BY cert_count DESC
        LIMIT :limit
        """
    )
    with _session() as sess:
        rows = sess.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# 5. get_card_population
# ---------------------------------------------------------------------------


def get_card_population(
    sport: str, year: str, set_title: str, card_name: str
) -> dict[str, Any]:
    """
    Return the full grade distribution for a specific card.

    Returns a dict with keys:
        sport, year, set_title, card_name,
        total_graded, grades (list of {grade, count, pct}),
        highest_grade, most_common_grade
    """
    sql = text(
        """
        SELECT
            cgr.tag_grade,
            COUNT(cgr.cert_number) AS count
        FROM card_grade_rows cgr
        WHERE cgr.sport      = :sport
          AND cgr.year       = :year
          AND cgr.set_title  = :set_title
          AND cgr.card_name  = :card_name
          AND cgr.is_active  = true
        GROUP BY cgr.tag_grade
        ORDER BY cgr.tag_grade DESC NULLS LAST
        """
    )
    params = {
        "sport": sport,
        "year": year,
        "set_title": set_title,
        "card_name": card_name,
    }
    with _session() as sess:
        rows = sess.execute(sql, params).fetchall()

    if not rows:
        return {
            "sport": sport,
            "year": year,
            "set_title": set_title,
            "card_name": card_name,
            "total_graded": 0,
            "grades": [],
            "highest_grade": None,
            "most_common_grade": None,
        }

    grade_data = [{"grade": r.tag_grade, "count": r.count} for r in rows]
    total = sum(g["count"] for g in grade_data)

    for g in grade_data:
        g["pct"] = round(g["count"] / total * 100, 1) if total else 0.0

    most_common = max(grade_data, key=lambda g: g["count"])

    return {
        "sport": sport,
        "year": year,
        "set_title": set_title,
        "card_name": card_name,
        "total_graded": total,
        "grades": grade_data,
        "highest_grade": grade_data[0]["grade"] if grade_data else None,
        "most_common_grade": most_common["grade"],
    }


# ---------------------------------------------------------------------------
# 6. get_set_population_summary
# ---------------------------------------------------------------------------


def get_set_population_summary(
    sport: str, year: str, set_title: str
) -> dict[str, Any]:
    """
    Return aggregate grade distribution for all cards in a set.

    Returns a dict with keys:
        sport, year, set_title,
        total_graded, unique_cards,
        grades (list of {grade, count, pct})
    """
    sql = text(
        """
        SELECT
            cgr.tag_grade,
            COUNT(cgr.cert_number)      AS count,
            COUNT(DISTINCT cgr.card_name) AS unique_cards
        FROM card_grade_rows cgr
        WHERE cgr.sport     = :sport
          AND cgr.year      = :year
          AND cgr.set_title = :set_title
          AND cgr.is_active = true
        GROUP BY cgr.tag_grade
        ORDER BY cgr.tag_grade DESC NULLS LAST
        """
    )
    params = {"sport": sport, "year": year, "set_title": set_title}
    with _session() as sess:
        rows = sess.execute(sql, params).fetchall()

    total = sum(r.count for r in rows)
    unique_cards = max((r.unique_cards for r in rows), default=0)

    grade_data = [
        {
            "grade": r.tag_grade,
            "count": r.count,
            "pct": round(r.count / total * 100, 1) if total else 0.0,
        }
        for r in rows
    ]

    return {
        "sport": sport,
        "year": year,
        "set_title": set_title,
        "total_graded": total,
        "unique_cards": unique_cards,
        "grades": grade_data,
    }


# ---------------------------------------------------------------------------
# 7. get_sport_overview
# ---------------------------------------------------------------------------


def get_sport_overview(sport: str) -> dict[str, Any]:
    """
    Return a high-level summary for a sport.

    Returns a dict with keys:
        sport, year_count, set_count, card_count,
        total_graded, grade_breakdown (list of {grade, count, pct}),
        years (sorted list of years)
    """
    counts_sql = text(
        """
        SELECT
            COUNT(DISTINCT cgr.year)       AS year_count,
            COUNT(DISTINCT cgr.set_title)  AS set_count,
            COUNT(DISTINCT cgr.card_name)  AS card_count,
            COUNT(cgr.cert_number)         AS total_graded
        FROM card_grade_rows cgr
        WHERE cgr.sport     = :sport
          AND cgr.is_active = true
        """
    )
    grade_sql = text(
        """
        SELECT
            cgr.tag_grade,
            COUNT(cgr.cert_number) AS count
        FROM card_grade_rows cgr
        WHERE cgr.sport     = :sport
          AND cgr.is_active = true
        GROUP BY cgr.tag_grade
        ORDER BY cgr.tag_grade DESC NULLS LAST
        """
    )
    years_sql = text(
        """
        SELECT year FROM years_index
        WHERE sport = :sport AND is_active = true
        ORDER BY year DESC
        """
    )
    params = {"sport": sport}
    with _session() as sess:
        counts_row = sess.execute(counts_sql, params).fetchone()
        grade_rows = sess.execute(grade_sql, params).fetchall()
        year_rows = sess.execute(years_sql, params).fetchall()

    total = counts_row.total_graded if counts_row else 0
    grade_data = [
        {
            "grade": r.tag_grade,
            "count": r.count,
            "pct": round(r.count / total * 100, 1) if total else 0.0,
        }
        for r in grade_rows
    ]

    return {
        "sport": sport,
        "year_count": counts_row.year_count if counts_row else 0,
        "set_count": counts_row.set_count if counts_row else 0,
        "card_count": counts_row.card_count if counts_row else 0,
        "total_graded": total,
        "grade_breakdown": grade_data,
        "years": [r.year for r in year_rows],
    }


# ---------------------------------------------------------------------------
# 8. lookup_cert
# ---------------------------------------------------------------------------


def lookup_cert(cert_number: str) -> dict[str, Any] | None:
    """
    Look up a specific certificate number.

    Returns a dict with full card/grade details, or None if not found.
    Keys: cert_number, sport, year, set_title, card_name,
          tag_grade, rank, rank_by_grade, chronology,
          completed_date_iso, card_url, report_url
    """
    sql = text(
        """
        SELECT
            cert_number, sport, year, set_title, card_name,
            tag_grade, rank, rank_by_grade, chronology, chron_by_grade,
            completed_date_iso, card_url, report_url
        FROM card_grade_rows
        WHERE cert_number = :cert_number
          AND is_active   = true
        LIMIT 1
        """
    )
    with _session() as sess:
        row = sess.execute(sql, {"cert_number": cert_number}).fetchone()
    if row is None:
        return None
    return _row_to_dict(row)


# ---------------------------------------------------------------------------
# 9. get_top_graded_cards
# ---------------------------------------------------------------------------


def get_top_graded_cards(
    grade: str,
    sport: str | None = None,
    year: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Return cards with the most graded copies at a specific grade.

    Returns a list of dicts with keys:
        sport, year, set_title, card_name, population
    Ordered by population descending.
    """
    filters = "cgr.tag_grade = :grade AND cgr.is_active = true"
    params: dict[str, Any] = {"grade": grade, "limit": limit}

    if sport:
        filters += " AND cgr.sport = :sport"
        params["sport"] = sport
    if year:
        filters += " AND cgr.year = :year"
        params["year"] = year

    sql = text(
        f"""
        SELECT
            cgr.sport,
            cgr.year,
            cgr.set_title,
            cgr.card_name,
            COUNT(cgr.cert_number) AS population
        FROM card_grade_rows cgr
        WHERE {filters}
        GROUP BY cgr.sport, cgr.year, cgr.set_title, cgr.card_name
        ORDER BY population DESC
        LIMIT :limit
        """
    )
    with _session() as sess:
        rows = sess.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# 10. get_database_stats
# ---------------------------------------------------------------------------


def get_database_stats() -> dict[str, Any]:
    """
    Return overall database health and content statistics.

    Returns a dict with keys:
        total_certs, total_sports, total_years, total_sets,
        total_cards, last_discovered, database_dialect
    """
    stats_sql = text(
        """
        SELECT
            (SELECT COUNT(*)           FROM card_grade_rows WHERE is_active = true) AS total_certs,
            (SELECT COUNT(DISTINCT sport) FROM years_index  WHERE is_active = true) AS total_sports,
            (SELECT COUNT(*)           FROM years_index     WHERE is_active = true) AS total_years,
            (SELECT COUNT(*)           FROM sets_per_year   WHERE is_active = true) AS total_sets,
            (SELECT COUNT(*)           FROM cards_per_set   WHERE is_active = true) AS total_cards,
            (SELECT MAX(discovered_at) FROM card_grade_rows WHERE is_active = true) AS last_discovered
        """
    )
    with _session() as sess:
        row = sess.execute(stats_sql).fetchone()

    d = _row_to_dict(row) if row else {}
    d["database_dialect"] = _db_dialect
    return d
