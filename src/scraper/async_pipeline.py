#!/usr/bin/env python3
"""
High-performance async scraping pipeline with all optimizations.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
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

else:
    ExceptionGroup = BaseExceptionGroup

from .async_db import AsyncBulkOperations, AsyncDatabasePool
from .async_scraper import AsyncWebScraper
from .cache_manager import ScrapingCacheManager
from .monitoring import get_monitoring_manager, profile_function


class AsyncPipelineConfig:
    """Configuration for the async pipeline."""

    def __init__(
        self,
        max_concurrent_requests: int = 10,
        max_concurrent_db_operations: int = 5,
        rate_limit: float = 1.0,
        batch_size: int = 100,
        enable_caching: bool = True,
        enable_monitoring: bool = True,
        cache_ttl: int = 3600,
        db_pool_size: int = 20,
        dry_run: bool = False,
        start_from: str = "category",
        year_filter: list[str] | None = None,
        set_filter: list[str] | None = None,
        card_filter: list[str] | None = None,
    ):
        """Initialize pipeline configuration."""
        self.max_concurrent_requests = max_concurrent_requests
        self.max_concurrent_db_operations = max_concurrent_db_operations
        self.rate_limit = rate_limit
        self.batch_size = batch_size
        self.enable_caching = enable_caching
        self.enable_monitoring = enable_monitoring
        self.cache_ttl = cache_ttl
        self.db_pool_size = db_pool_size
        self.dry_run = dry_run
        self.start_from = start_from
        self.year_filter = year_filter or []
        self.set_filter = set_filter or []
        self.card_filter = card_filter or []


class AsyncScrapingPipeline:
    """High-performance async scraping pipeline."""

    def __init__(self, config: AsyncPipelineConfig):
        """Initialize async scraping pipeline."""
        self.config = config
        self.db_pool: AsyncDatabasePool | None = None
        self.bulk_ops: AsyncBulkOperations | None = None
        self.scraper: AsyncWebScraper | None = None
        self.cache: ScrapingCacheManager | None = None
        self.monitoring = get_monitoring_manager() if config.enable_monitoring else None

        # Statistics
        self.stats = {
            "categories_processed": 0,
            "years_processed": 0,
            "sets_processed": 0,
            "cards_processed": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    @profile_function("pipeline_initialize")
    async def initialize(self) -> None:
        """Initialize the pipeline components."""
        print("🚀 Initializing async scraping pipeline...")

        # Initialize database pool
        self.db_pool = AsyncDatabasePool(
            pool_size=self.config.db_pool_size,
            enable_postgres=True,
        )
        await self.db_pool.initialize()

        # Initialize bulk operations
        self.bulk_ops = AsyncBulkOperations(self.db_pool)

        # Initialize scraper
        self.scraper = AsyncWebScraper(
            max_concurrent=self.config.max_concurrent_requests,
            rate_limit=self.config.rate_limit,
            enable_cache=self.config.enable_caching,
            use_playwright_fallback=True,
        )
        await self.scraper.__aenter__()

        # Initialize cache if enabled
        if self.config.enable_caching:
            from .cache_manager import get_scraping_cache

            self.cache = get_scraping_cache()

        print("✅ Pipeline initialization complete")

    @profile_function("pipeline_cleanup")
    async def cleanup(self) -> None:
        """Cleanup pipeline resources."""
        print("🧹 Cleaning up pipeline resources...")

        if self.scraper:
            await self.scraper.__aexit__(None, None, None)

        if self.db_pool:
            await self.db_pool.close()

        if self.monitoring:
            await self.monitoring.save_report()
            await self.monitoring.cleanup()

        # Print final statistics
        self.print_final_stats()

    @profile_function("scrape_categories")
    async def scrape_categories(
        self, base_url: str = "https://my.taggrading.com/pop-report"
    ) -> list[dict[str, Any]]:
        """Scrape categories from the main page."""
        print("📂 Scraping categories...")

        # Check cache first
        if self.cache:
            cached_categories = await self.cache.get_categories("all")
            if cached_categories:
                print(f"✅ Found {len(cached_categories)} cached categories")
                return cached_categories

        # Scrape categories
        categories = await self.scraper.extract_categories_async(base_url)

        # Cache the results
        if self.cache and categories:
            await self.cache.set_categories("all", categories)

        print(f"✅ Scraped {len(categories)} categories")
        return categories

    @profile_function("scrape_years")
    async def scrape_years(self, sport: str) -> list[dict[str, Any]]:
        """Scrape years for a sport."""
        print(f"📅 Scraping years for {sport}...")

        # Check cache first
        if self.cache:
            cached_years = await self.cache.get_years(sport)
            if cached_years:
                print(f"✅ Found {len(cached_years)} cached years for {sport}")
                return cached_years

        # Scrape years
        sport_url = f"https://my.taggrading.com/pop-report/{sport}"
        years = await self.scraper.extract_years_async(sport_url)

        # Apply year filter if specified
        if self.config.year_filter:
            years = [y for y in years if y["year"] in self.config.year_filter]

        # Cache the results
        if self.cache and years:
            await self.cache.set_years(sport, years)

        print(f"✅ Scraped {len(years)} years for {sport}")
        return years

    @profile_function("scrape_sets")
    async def scrape_sets(self, sport: str, year: str) -> list[dict[str, Any]]:
        """Scrape sets for a sport/year."""
        print(f"📦 Scraping sets for {sport} {year}...")

        # Check cache first
        if self.cache:
            cached_sets = await self.cache.get_sets(sport, year)
            if cached_sets:
                print(f"✅ Found {len(cached_sets)} cached sets for {sport} {year}")
                return cached_sets

        # Scrape sets
        year_url = f"https://my.taggrading.com/pop-report/{sport}/{year}"
        sets = await self.scraper.extract_sets_async(year_url)

        # Apply set filter if specified
        if self.config.set_filter:
            sets = [s for s in sets if s["set_name"] in self.config.set_filter]

        # Cache the results
        if self.cache and sets:
            await self.cache.set_sets(sport, year, sets)

        print(f"✅ Scraped {len(sets)} sets for {sport} {year}")
        return sets

    @profile_function("scrape_cards")
    async def scrape_cards(
        self, sport: str, year: str, set_name: str
    ) -> list[dict[str, Any]]:
        """Scrape cards for a sport/year/set."""
        print(f"🃏 Scraping cards for {sport} {year} {set_name}...")

        # Check cache first
        if self.cache:
            cached_cards = await self.cache.get_cards(sport, year, set_name)
            if cached_cards:
                print(
                    f"✅ Found {len(cached_cards)} cached cards for {sport} {year} {set_name}"
                )
                return cached_cards

        # Scrape cards
        set_url = f"https://my.taggrading.com/pop-report/{sport}/{year}/{set_name}"
        cards = await self.scraper.extract_cards_async(set_url)

        # Apply card filter if specified
        if self.config.card_filter:
            cards = [c for c in cards if c["card_name"] in self.config.card_filter]

        # Cache the results
        if self.cache and cards:
            await self.cache.set_cards(sport, year, set_name, cards)

        print(f"✅ Scraped {len(cards)} cards for {sport} {year} {set_name}")
        return cards

    @profile_function("scrape_card_details")
    async def scrape_card_details(self, card_url: str) -> dict[str, Any]:
        """Scrape card details from a card URL."""
        # Check cache first
        if self.cache:
            cached_details = await self.cache.get_card_details(card_url)
            if cached_details:
                return cached_details

        # Scrape card details
        details = await self.scraper.extract_card_details_async(card_url)

        # Cache the results
        if self.cache and details:
            await self.cache.set_card_details(card_url, details)

        return details

    @profile_function("process_cards_batch")
    async def process_cards_batch(
        self, cards: list[dict[str, Any]], sport: str, year: str, set_name: str
    ) -> None:
        """Process a batch of cards efficiently."""
        if not cards:
            return

        # Extract card URLs
        card_urls = [card["card_url"] for card in cards if card.get("card_url")]

        if not card_urls:
            return

        # Fetch card details concurrently
        print(f"🔄 Processing {len(card_urls)} card details concurrently...")

        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        results: list[tuple[str, dict[str, Any] | None]] = []
        successful_cards = 0

        async def fetch_card_detail(url: str) -> None:
            async with semaphore:
                try:
                    details = await self.scrape_card_details(url)
                    results.append((url, details))
                    if details:
                        nonlocal successful_cards
                        successful_cards += 1
                        self.stats["cards_processed"] += 1
                except Exception as e:
                    print(f"❌ Error fetching card details for {url}: {e}")
                    if self.monitoring:
                        self.monitoring.metrics.record_scraping_error(
                            str(type(e).__name__), "card_details"
                        )
                    results.append((url, None))
                    self.stats["errors"] += 1

        # Use TaskGroup for better concurrency control and error handling
        try:
            async with asyncio.TaskGroup() as tg:
                for url in card_urls:
                    tg.create_task(fetch_card_detail(url))
        except ExceptionGroup as eg:
            # Log any unhandled exceptions from the task group (Python 3.11+)
            for exc in eg.exceptions:
                print(f"❌ Unhandled task exception: {exc}")
                self.stats["errors"] += 1
        except Exception as e:
            # Fallback for Python < 3.11 or non-ExceptionGroup exceptions
            print(f"❌ Unhandled task exception: {e}")
            self.stats["errors"] += 1

        print(
            f"✅ Successfully processed {successful_cards}/{len(card_urls)} card details"
        )

    @profile_function("run_pipeline")
    async def run_pipeline(self, sports: list[str] | None = None) -> dict[str, Any]:
        """Run the complete scraping pipeline."""
        self.stats["start_time"] = datetime.datetime.now()
        print(f"🚀 Starting async scraping pipeline at {self.stats['start_time']}")
        print(
            f"Configuration: {self.config.max_concurrent_requests} concurrent requests, "
            f"{self.config.rate_limit}s rate limit, batch size {self.config.batch_size}"
        )

        try:
            # Get categories/sports to scrape
            if sports:
                categories = [{"name": sport} for sport in sports]
            else:
                categories = await self.scrape_categories()

            # Process each category/sport
            for category in categories:
                sport = category["name"]

                if sport.upper() == "TOTALS":
                    continue

                print(f"\n🏈 Processing sport: {sport}")
                self.stats["categories_processed"] += 1

                # Scrape years for this sport
                years = await self.scrape_years(sport)

                for year_data in years:
                    year = year_data["year"]

                    if year.upper() == "TOTALS":
                        continue

                    print(f"\n📅 Processing year: {sport} {year}")
                    self.stats["years_processed"] += 1

                    # Scrape sets for this year
                    sets = await self.scrape_sets(sport, year)

                    for set_data in sets:
                        set_name = set_data["set_name"]

                        if set_name.upper() == "TOTALS":
                            continue

                        print(f"\n📦 Processing set: {sport} {year} {set_name}")
                        self.stats["sets_processed"] += 1

                        # Scrape cards for this set
                        cards = await self.scrape_cards(sport, year, set_name)

                        if cards:
                            # Process cards in batches
                            await self.process_cards_batch(cards, sport, year, set_name)

        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            self.stats["errors"] += 1
            if self.monitoring:
                self.monitoring.metrics.record_scraping_error(
                    str(type(e).__name__), "pipeline"
                )
            raise

        finally:
            self.stats["end_time"] = datetime.datetime.now()

        return self.get_pipeline_stats()

    def get_pipeline_stats(self) -> dict[str, Any]:
        """Get pipeline statistics."""
        runtime = None
        if self.stats["start_time"] and self.stats["end_time"]:
            runtime = (
                self.stats["end_time"] - self.stats["start_time"]
            ).total_seconds()

        return {
            "categories_processed": self.stats["categories_processed"],
            "years_processed": self.stats["years_processed"],
            "sets_processed": self.stats["sets_processed"],
            "cards_processed": self.stats["cards_processed"],
            "errors": self.stats["errors"],
            "runtime_seconds": runtime,
            "start_time": self.stats["start_time"].isoformat()
            if self.stats["start_time"]
            else None,
            "end_time": self.stats["end_time"].isoformat()
            if self.stats["end_time"]
            else None,
        }

    def print_final_stats(self) -> None:
        """Print final pipeline statistics."""
        stats = self.get_pipeline_stats()

        print("\n" + "=" * 80)
        print("📊 PIPELINE COMPLETION STATISTICS")
        print("=" * 80)
        print(f"Categories processed: {stats['categories_processed']}")
        print(f"Years processed: {stats['years_processed']}")
        print(f"Sets processed: {stats['sets_processed']}")
        print(f"Cards processed: {stats['cards_processed']}")
        print(f"Errors encountered: {stats['errors']}")

        if stats["runtime_seconds"]:
            runtime_str = str(datetime.timedelta(seconds=int(stats["runtime_seconds"])))
            print(f"Total runtime: {runtime_str}")

        if self.scraper:
            js_urls = self.scraper.get_js_required_urls()
            if js_urls:
                print(f"JavaScript-required URLs: {len(js_urls)}")

        print("=" * 80)


async def main():
    """Main entry point for the async pipeline."""
    parser = argparse.ArgumentParser(
        description="High-performance async TAG Grading scraper pipeline"
    )

    # Concurrency and performance options
    parser.add_argument(
        "--max-concurrent-requests",
        type=int,
        default=10,
        help="Maximum concurrent HTTP requests (default: 10)",
    )
    parser.add_argument(
        "--max-concurrent-db-operations",
        type=int,
        default=5,
        help="Maximum concurrent database operations (default: 5)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Rate limit between requests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for database operations (default: 100)",
    )
    parser.add_argument(
        "--db-pool-size",
        type=int,
        default=20,
        help="Database connection pool size (default: 20)",
    )

    # Caching options
    parser.add_argument(
        "--enable-caching",
        action="store_true",
        default=True,
        help="Enable response caching (default: True)",
    )
    parser.add_argument(
        "--disable-caching", action="store_true", help="Disable response caching"
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=3600,
        help="Cache time-to-live in seconds (default: 3600)",
    )

    # Monitoring options
    parser.add_argument(
        "--enable-monitoring",
        action="store_true",
        default=True,
        help="Enable performance monitoring (default: True)",
    )
    parser.add_argument(
        "--disable-monitoring",
        action="store_true",
        help="Disable performance monitoring",
    )

    # Execution options
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run mode (no database writes)"
    )
    parser.add_argument(
        "--sports", nargs="+", help="Specific sports to scrape (e.g., Baseball Hockey)"
    )
    parser.add_argument("--year-filter", nargs="+", help="Filter to specific years")
    parser.add_argument("--set-filter", nargs="+", help="Filter to specific sets")
    parser.add_argument("--card-filter", nargs="+", help="Filter to specific cards")

    args = parser.parse_args()

    # Create configuration
    config = AsyncPipelineConfig(
        max_concurrent_requests=args.max_concurrent_requests,
        max_concurrent_db_operations=args.max_concurrent_db_operations,
        rate_limit=args.rate_limit,
        batch_size=args.batch_size,
        enable_caching=args.enable_caching and not args.disable_caching,
        enable_monitoring=args.enable_monitoring and not args.disable_monitoring,
        cache_ttl=args.cache_ttl,
        db_pool_size=args.db_pool_size,
        dry_run=args.dry_run,
        year_filter=args.year_filter,
        set_filter=args.set_filter,
        card_filter=args.card_filter,
    )

    # Run the pipeline
    async with AsyncScrapingPipeline(config) as pipeline:
        try:
            await pipeline.run_pipeline(args.sports)
            print("✅ Pipeline completed successfully!")
            return 0
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
