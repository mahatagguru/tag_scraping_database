#!/usr/bin/env python3
"""
Optimized scraping pipeline with increased parallelism and reduced delays.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import sys
import time
from typing import Any, Dict, List, Optional

from db import SessionLocal
from scraper.card_crawler import extract_card_urls, extract_cards, fetch_rendered_html as fetch_card_html
from scraper.card_detail_crawler import (
    extract_card_details,
    extract_cert_urls,
    fetch_rendered_html as fetch_card_detail_html,
)
from scraper.crawler import extract_categories, extract_category_urls, fetch_rendered_html as fetch_category_html
from scraper.db_helpers import (
    upsert_card,
    upsert_category,
    upsert_category_total,
    upsert_population_report,
    upsert_set,
    upsert_set_total,
    upsert_year,
    upsert_year_total,
)
from scraper.set_crawler import extract_set_urls, extract_sets, fetch_rendered_html as fetch_set_html
from scraper.url_builder import build_set_page_url
from scraper.year_crawler import extract_year_urls, extract_years, fetch_rendered_html as fetch_year_html

CATEGORY_URL = "https://my.taggrading.com/pop-report"
BASE_URL = "https://my.taggrading.com"

# Configuration for optimization
MAX_WORKERS = 16  # Increased from 8
MIN_DELAY = 0.1  # Reduced from 1 second
BATCH_SIZE = 50  # Process cards in batches


def process_card_url(
    card_url: str,
    session: Any,
    db_cat: Any,
    db_year: Any,
    db_set: Any,
    snapshot_date: str,
) -> None:
    """Process a single card URL with error handling."""
    try:
        card_html = fetch_card_html(card_url)
        card_details = extract_card_details(card_html)

        for row in card_details["table_rows"]:
            card_uid = row.get("cert_number") or row.get("view_report") or card_url
            upsert_card(
                session,
                card_uid=card_uid,
                category_id=db_cat.id,
                year_id=db_year.id,
                set_id=db_set.id,
                card_number=None,
                player=card_details["player_name"],
                detail_url=card_url,
                image_url=card_details["card_image_url"],
                subset_name=card_details["subset_name"],
                variation=card_details["variation"],
                cert_number=row.get("cert_number"),
            )

            # Process population reports
            tag_grade = row.get("tag_grade")
            completed = row.get("completed")
            population_count = (
                int(completed.replace("-", "").replace("/", "").replace(" ", ""))
                if completed
                and completed.replace("-", "")
                .replace("/", "")
                .replace(" ", "")
                .isdigit()
                else None
            )

            if tag_grade and population_count is not None:
                upsert_population_report(
                    session,
                    card_uid=card_uid,
                    grade_label=tag_grade,
                    snapshot_date=snapshot_date,
                    population_count=population_count,
                    total_graded=population_count,
                )

                # Also add to 'ALL' category
                upsert_population_report(
                    session,
                    card_uid=card_uid,
                    grade_label="ALL",
                    snapshot_date=snapshot_date,
                    population_count=population_count,
                    total_graded=population_count,
                )

    except Exception as e:
        print(f"          Error processing card {card_url}: {e}")


def process_set_parallel(
    session: Any,
    db_cat: Any,
    db_year: Any,
    s: Dict[str, Any],
    cat_name: str,
    year: str,
    snapshot_date: str,
) -> int:
    """Process a single set with parallel card processing."""
    try:
        db_set = upsert_set(
            session, category_id=db_cat.id, year_id=db_year.id, set_name=s["set_name"]
        )

        # Set total (if available)
        total_graded = (
            int(s["grades"][-1]) if s["grades"] and s["grades"][-1].isdigit() else None
        )
        if total_graded is not None:
            upsert_population_report(
                session,
                card_uid="ALL",
                grade_label="ALL",
                snapshot_date=snapshot_date,
                population_count=total_graded,
                total_graded=total_graded,
            )

        # Use the new URL builder for correct URL construction
        set_page_url = build_set_page_url(cat_name, year, s["set_name"], BASE_URL)

        print(f"          Fetching set page: {set_page_url}")
        set_page_html = fetch_card_html(set_page_url)
        card_urls = extract_card_urls(set_page_html)
        print(f"          Found {len(card_urls)} card URLs.")

        if card_urls:
            # Process cards in parallel with increased workers
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = []
                for card_url in card_urls:
                    future = executor.submit(
                        process_card_url,
                        card_url,
                        session,
                        db_cat,
                        db_year,
                        db_set,
                        snapshot_date,
                    )
                    futures.append(future)

                # Wait for all cards to complete
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"          Card processing error: {e}")

            session.commit()  # Commit after all cards in set
            return len(card_urls)
        else:
            print(f"          No cards found for set {s['set_name']}")
            return 0

    except Exception as e:
        print(f"        Error processing set {s['set_name']}: {e}")
        return 0


def optimized_pipeline() -> None:
    """Optimized pipeline with increased parallelism."""
    print("Starting optimized scraping pipeline...")
    print(
        f"Configuration: {MAX_WORKERS} workers, {MIN_DELAY}s delays, batch size {BATCH_SIZE}"
    )

    snapshot_date = datetime.datetime.now(datetime.timezone.utc).isoformat()
    session = SessionLocal()

    try:
        # Get categories
        print("1. Fetching categories...")
        cat_html = fetch_category_html(CATEGORY_URL)
        categories = extract_categories(cat_html)
        print(f"   ✓ Found {len(categories)} categories")

        for cat in categories:
            if cat["name"].strip().upper() == "TOTALS":
                print(
                    f"   CATEGORY TOTALS: sets: {cat.get('num_sets', 'N/A')} | items: {cat.get('total_items', 'N/A')} | graded: {cat.get('total_graded', 'N/A')}"
                )
                continue

            print(f"   Category: {cat['name']} | img: {cat.get('image_url', 'N/A')}")

            try:
                db_cat = upsert_category(
                    session, name=cat["name"], img=cat.get("image_url")
                )

                # Get years for this category
                cat_url = f"{BASE_URL}/pop-report/{cat['name'].title()}"
                print(f"      Fetching years for {cat['name']}...")

                year_html = fetch_year_html(cat_url)
                years = extract_years(year_html)
                print(f"      Found {len(years)} years.")

                for y in years:
                    if y["year"].strip().upper() == "TOTALS":
                        print(
                            f"        YEAR TOTALS: sets: {y['num_sets']} | items: {y['total_items']} | graded: {y['total_graded']}"
                        )
                        continue

                    print(
                        f"        Year: {y['year']} | sets: {y['num_sets']} | items: {y['total_items']} | graded: {y['total_graded']}"
                    )

                    try:
                        db_year = upsert_year(
                            session, category_id=db_cat.id, year=int(y["year"])
                        )

                        # Year total
                        total_graded = (
                            int(y["total_graded"])
                            if y["total_graded"] and y["total_graded"].isdigit()
                            else None
                        )
                        if total_graded is not None:
                            upsert_population_report(
                                session,
                                card_uid="ALL",
                                grade_label="ALL",
                                snapshot_date=snapshot_date,
                                population_count=total_graded,
                                total_graded=total_graded,
                            )

                        if y["num_sets"] or y["total_items"] or y["total_graded"]:
                            upsert_year_total(
                                session,
                                year_id=db_year.id,
                                num_sets=int(y["num_sets"])
                                if y["num_sets"].isdigit()
                                else None,
                                total_items=int(y["total_items"])
                                if y["total_items"].isdigit()
                                else None,
                                total_graded=total_graded,
                            )

                        # Get sets for this year
                        set_url = (
                            f"{BASE_URL}/pop-report/{cat['name'].title()}/{y['year']}"
                        )
                        print(
                            f"          Fetching sets for {cat['name']} {y['year']}..."
                        )

                        set_html = fetch_set_html(set_url)
                        sets = extract_sets(set_html)
                        print(f"          Found {len(sets)} sets.")

                        # Process sets in parallel
                        set_futures = []
                        with ThreadPoolExecutor(max_workers=8) as set_executor:
                            for s in sets:
                                if s["set_name"].strip().upper() == "TOTALS":
                                    print(
                                        f"            SET TOTALS: grades: {s['grades']}"
                                    )
                                    continue

                                print(
                                    f"            Set: {s['set_name']} | grades: {s['grades']}"
                                )
                                future = set_executor.submit(
                                    process_set_parallel,
                                    session,
                                    db_cat,
                                    db_year,
                                    s,
                                    cat["name"],
                                    y["year"],
                                    snapshot_date,
                                )
                                set_futures.append(future)

                            # Wait for all sets to complete
                            total_cards = 0
                            for future in as_completed(set_futures):
                                try:
                                    cards_processed = future.result()
                                    if cards_processed is not None:
                                        total_cards += cards_processed
                                except Exception as e:
                                    print(f"            Set processing error: {e}")

                        print(
                            f"          ✓ Processed {total_cards} total cards for {cat['name']} {y['year']}"
                        )

                    except Exception as e:
                        print(f"        Error processing year {y['year']}: {e}")
                        continue

                    time.sleep(MIN_DELAY)  # Reduced delay

            except Exception as e:
                print(f"      Error processing category {cat['name']}: {e}")
                continue

            session.commit()  # Commit after each category
            time.sleep(MIN_DELAY)  # Reduced delay

    except Exception as e:
        print("Pipeline error:", e)
        import traceback

        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

    print("✅ Optimized pipeline completed!")


if __name__ == "__main__":
    optimized_pipeline()
