#!/usr/bin/env python3
"""
New Multi-Level Scraping Pipeline

Integrates the complete multi-level scraping system:
1. Scrapes Years index from sport pages
2. Scrapes Sets from each year page
3. Handles TOTALS at all levels
4. Stores everything in the new database tables

Usage:
    python3 new_pipeline.py --sport Baseball
    python3 new_pipeline.py --sport Hockey  
    python3 new_pipeline.py --all-sports
    python3 new_pipeline.py --sport Baseball --dry-run
"""

import argparse
import datetime
from typing import Any, Dict, List, Optional

# Add project root to path
import os
import sys
import time
from urllib.parse import urljoin

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.multi_level_orchestrator import scrape_multiple_sports, scrape_sport

BASE_URL = "https://my.taggrading.com"

# Known sports on the platform
KNOWN_SPORTS = [
    "Baseball",
    "Hockey",
    "Basketball",
    "Football",
    "Soccer",
    "Golf",
    "Racing",
    "Wrestling",
    "Gaming",
    "Non-Sport",
]


def build_sport_url(sport: str) -> str:
    """Build the sport index URL from sport name"""
    return urljoin(BASE_URL, f"/pop-report/{sport}")


def scrape_single_sport(
    sport: str, concurrency: int = 3, delay: float = 1.0, dry_run: bool = False
) -> Any:
    """
    Scrape a single sport completely.

    Args:
        sport: Sport name (e.g., "Baseball")
        concurrency: Max parallel requests
        delay: Delay between requests
        dry_run: If True, only print what would be done

    Returns:
        dict: Scraping summary
    """
    sport_url = build_sport_url(sport)

    print(f"\n{'='*60}")
    print(f"SCRAPING SPORT: {sport}")
    print(f"URL: {sport_url}")
    print(f"Concurrency: {concurrency}")
    print(f"Delay: {delay}s")
    print(f"Dry Run: {dry_run}")
    print("=" * 60)

    if dry_run:
        print("🔍 DRY RUN MODE - No actual scraping or database writes")
        print(f"Would scrape: {sport_url}")
        return {
            "sport": sport,
            "sport_url": sport_url,
            "dry_run": True,
            "status": "simulated",
        }

    try:
        start_time = time.time()
        summary = scrape_sport(sport_url, concurrency=concurrency, delay=delay)
        end_time = time.time()

        summary.update(
            {
                "sport": sport,
                "status": "success",
                "total_duration": end_time - start_time,
            }
        )

        return summary

    except Exception as e:
        print(f"❌ Error scraping {sport}: {e}")
        return {
            "sport": sport,
            "sport_url": sport_url,
            "status": "error",
            "error": str(e),
        }


def scrape_all_sports(
    concurrency: int = 3, delay: float = 1.0, dry_run: bool = False
) -> Any:
    """
    Scrape all known sports.

    Args:
        concurrency: Max parallel requests per sport
        delay: Delay between requests
        dry_run: If True, only print what would be done

    Returns:
        list: List of scraping summaries
    """
    print(f"\n{'='*80}")
    print("SCRAPING ALL SPORTS")
    print(f"Sports: {', '.join(KNOWN_SPORTS)}")
    print(f"Total: {len(KNOWN_SPORTS)} sports")
    print(f"Concurrency: {concurrency}")
    print(f"Delay: {delay}s")
    print(f"Dry Run: {dry_run}")
    print("=" * 80)

    if dry_run:
        print("🔍 DRY RUN MODE - No actual scraping or database writes")
        summaries = []
        for sport in KNOWN_SPORTS:
            sport_url = build_sport_url(sport)
            print(f"Would scrape: {sport} -> {sport_url}")
            summaries.append(
                {
                    "sport": sport,
                    "sport_url": sport_url,
                    "dry_run": True,
                    "status": "simulated",
                }
            )
        return summaries

    sport_urls = [build_sport_url(sport) for sport in KNOWN_SPORTS]
    summaries = scrape_multiple_sports(sport_urls, concurrency=concurrency, delay=delay)

    # Add sport names to summaries
    for i, summary in enumerate(summaries):
        summary["sport"] = KNOWN_SPORTS[i]

    return summaries


def print_final_summary(summaries: List[Dict[str, Any]]) -> None:
    """Print a comprehensive final summary"""
    print(f"\n{'='*80}")
    print("FINAL PIPELINE SUMMARY")
    print("=" * 80)

    total_sports = len(summaries)
    successful_sports = 0
    failed_sports = 0
    total_years = 0
    total_sets = 0
    total_duration = 0

    for summary in summaries:
        sport = summary.get("sport", "Unknown")
        status = summary.get("status", "unknown")

        if status == "success":
            successful_sports += 1
            total_years += summary.get("years_found", 0)
            total_sets += summary.get("total_sets", 0)
            total_duration += summary.get("duration_seconds", 0)

            print(
                f"✅ {sport}: {summary.get('years_found', 0)} years, {summary.get('total_sets', 0)} sets"
            )

        elif status == "error":
            failed_sports += 1
            print(f"❌ {sport}: FAILED - {summary.get('error', 'Unknown error')}")

        elif status == "simulated":
            print(f"🔍 {sport}: SIMULATED (dry run)")

        else:
            failed_sports += 1
            print(f"❓ {sport}: UNKNOWN STATUS")

    print(f"\n📊 STATISTICS:")
    print(f"   Total Sports: {total_sports}")
    print(f"   Successful: {successful_sports}")
    print(f"   Failed: {failed_sports}")

    if successful_sports > 0:
        print(f"   Total Years: {total_years}")
        print(f"   Total Sets: {total_sets}")
        print(f"   Total Duration: {total_duration:.1f}s")
        print(f"   Average Duration per Sport: {total_duration/successful_sports:.1f}s")

    success_rate = (successful_sports / total_sports) * 100 if total_sports > 0 else 0
    print(f"   Success Rate: {success_rate:.1f}%")

    print("=" * 80)

    if success_rate == 100:
        print("🎉 ALL SPORTS SCRAPED SUCCESSFULLY!")
    elif success_rate >= 80:
        print("✅ MOST SPORTS SCRAPED SUCCESSFULLY!")
    elif success_rate >= 50:
        print("⚠️  SOME SPORTS FAILED - Review errors above")
    else:
        print("❌ MANY SPORTS FAILED - Check configuration and network")


def main() -> None:
    """Main pipeline entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-Level Scraping Pipeline for TAG Grading Pop Reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 new_pipeline.py --sport Baseball
  python3 new_pipeline.py --sport Hockey --concurrency 5 --delay 0.5
  python3 new_pipeline.py --all-sports
  python3 new_pipeline.py --sport Baseball --dry-run
  python3 new_pipeline.py --all-sports --dry-run
        """,
    )

    # Main action options
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--sport", type=str, help="Scrape a single sport (e.g., Baseball, Hockey)"
    )
    action_group.add_argument(
        "--all-sports", action="store_true", help="Scrape all known sports"
    )

    # Configuration options
    parser.add_argument(
        "--concurrency", type=int, default=3, help="Max parallel requests (default: 3)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without actually doing it",
    )

    args = parser.parse_args()

    # Print startup info
    print("🚀 TAG GRADING MULTI-LEVEL SCRAPING PIPELINE")
    print(f"Started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Validate sport if provided
    if args.sport and args.sport not in KNOWN_SPORTS:
        print(f"⚠️  Warning: '{args.sport}' is not in the list of known sports.")
        print(f"Known sports: {', '.join(KNOWN_SPORTS)}")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != "y":
            print("Aborted.")
            sys.exit(1)

    # Run the appropriate scraping operation
    start_time = time.time()

    try:
        if args.sport:
            summaries: List[Any] = [
                scrape_single_sport(
                    args.sport,
                    concurrency=args.concurrency,
                    delay=args.delay,
                    dry_run=args.dry_run,
                )
            ]
        else:  # args.all_sports
            summaries = scrape_all_sports(
                concurrency=args.concurrency, delay=args.delay, dry_run=args.dry_run
            )

        end_time = time.time()
        total_pipeline_duration = end_time - start_time

        # Print final summary
        print_final_summary(summaries)

        print(f"\n⏱️  Total Pipeline Duration: {total_pipeline_duration:.1f} seconds")
        print(
            f"🏁 Pipeline completed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
