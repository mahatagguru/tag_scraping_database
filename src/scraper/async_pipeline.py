#!/usr/bin/env python3
"""
High-performance async scraping pipeline with all optimizations.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import sys
from typing import Any

from .async_db import AsyncBulkOperations, AsyncDatabasePool
from .compat import BaseExceptionGroup, ExceptionGroup

logger = logging.getLogger(__name__)
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
        logger.info("Initializing async scraping pipeline...")

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

        logger.info("Pipeline initialization complete")

    @profile_function("pipeline_cleanup")
    async def cleanup(self) -> None:
        """Cleanup pipeline resources."""
        logger.info("Cleaning up pipeline resources...")

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
        logger.info("Scraping categories...")

        # Check cache first
        if self.cache:
            cached_categories = await self.cache.get_categories("all")
            if cached_categories:
                logger.info("Found %d cached categories", len(cached_categories))
                return cached_categories

        # Scrape categories
        categories = await self.scraper.extract_categories_async(base_url)

        # Cache the results
        if self.cache and categories:
            await self.cache.set_categories("all", categories)

        logger.info("Scraped %d categories", len(categories))
        return categories

    @profile_function("scrape_years")
    async def scrape_years(self, sport: str) -> list[dict[str, Any]]:
        """Scrape years for a sport."""
        logger.info("Scraping years for %s...", sport)

        # Check cache first
        if self.cache:
            cached_years = await self.cache.get_years(sport)
            if cached_years:
                logger.info("Found %d cached years for %s", len(cached_years), sport)
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

        logger.info("Scraped %d years for %s", len(years), sport)
        return years

    @profile_function("scrape_sets")
    async def scrape_sets(self, sport: str, year: str) -> list[dict[str, Any]]:
        """Scrape sets for a sport/year."""
        logger.info("Scraping sets for %s %s...", sport, year)

        # Check cache first
        if self.cache:
            cached_sets = await self.cache.get_sets(sport, year)
            if cached_sets:
                logger.info("Found %d cached sets for %s %s", len(cached_sets), sport, year)
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

        logger.info("Scraped %d sets for %s %s", len(sets), sport, year)
        return sets

    @profile_function("scrape_cards")
    async def scrape_cards(
        self, sport: str, year: str, set_name: str
    ) -> list[dict[str, Any]]:
        """Scrape cards for a sport/year/set."""
        logger.info("Scraping cards for %s %s %s...", sport, year, set_name)

        # Check cache first
        if self.cache:
            cached_cards = await self.cache.get_cards(sport, year, set_name)
            if cached_cards:
                logger.info(
                    "Found %d cached cards for %s %s %s",
                    len(cached_cards), sport, year, set_name,
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

        logger.info("Scraped %d cards for %s %s %s", len(cards), sport, year, set_name)
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
        logger.info("Processing %d card details concurrently...", len(card_urls))

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
                    logger.error("Error fetching card details for %s: %s", url, e)
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
                logger.error("Unhandled task exception: %s", exc)
                self.stats["errors"] += 1
        except Exception as e:
            # Fallback for Python < 3.11 or non-ExceptionGroup exceptions
            logger.error("Unhandled task exception: %s", e)
            self.stats["errors"] += 1

        logger.info(
            "Successfully processed %d/%d card details",
            successful_cards, len(card_urls),
        )

    @profile_function("run_pipeline")
    async def run_pipeline(self, sports: list[str] | None = None) -> dict[str, Any]:
        """Run the complete scraping pipeline."""
        self.stats["start_time"] = datetime.datetime.now()
        logger.info("Starting async scraping pipeline at %s", self.stats["start_time"])
        logger.info(
            "Configuration: %d concurrent requests, %.1fs rate limit, batch size %d",
            self.config.max_concurrent_requests,
            self.config.rate_limit,
            self.config.batch_size,
        )

        # Lock protecting shared stats counters accessed from concurrent coroutines
        stats_lock = asyncio.Lock()

        async def process_set(sport: str, year: str, set_data: dict[str, Any]) -> None:
            set_name = set_data["set_name"]
            if set_name.upper() == "TOTALS":
                return
            logger.info("Processing set: %s %s %s", sport, year, set_name)
            async with stats_lock:
                self.stats["sets_processed"] += 1
            cards = await self.scrape_cards(sport, year, set_name)
            if cards:
                await self.process_cards_batch(cards, sport, year, set_name)

        async def process_year(sport: str, year_data: dict[str, Any]) -> None:
            year = year_data["year"]
            if year.upper() == "TOTALS":
                return
            logger.info("Processing year: %s %s", sport, year)
            async with stats_lock:
                self.stats["years_processed"] += 1
            sets = await self.scrape_sets(sport, year)
            # Process sets for this year concurrently
            async with asyncio.TaskGroup() as tg:
                for set_data in sets:
                    tg.create_task(process_set(sport, year, set_data))

        try:
            # Get categories/sports to scrape
            if sports:
                categories = [{"name": sport} for sport in sports]
            else:
                categories = await self.scrape_categories()

            # Process each category/sport (categories are processed sequentially to
            # avoid overwhelming the target server at the top level)
            for category in categories:
                sport = category["name"]
                if sport.upper() == "TOTALS":
                    continue

                logger.info("Processing sport: %s", sport)
                self.stats["categories_processed"] += 1
                years = await self.scrape_years(sport)

                # Process years concurrently within each sport
                try:
                    async with asyncio.TaskGroup() as tg:
                        for year_data in years:
                            tg.create_task(process_year(sport, year_data))
                except ExceptionGroup as eg:
                    for exc in eg.exceptions:
                        logger.error("Error processing year: %s", exc)
                        async with stats_lock:
                            self.stats["errors"] += 1

        except Exception as e:
            logger.error("Pipeline error: %s", e)
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
        """Log final pipeline statistics."""
        stats = self.get_pipeline_stats()

        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETION STATISTICS")
        logger.info("=" * 60)
        logger.info("Categories processed: %d", stats["categories_processed"])
        logger.info("Years processed: %d", stats["years_processed"])
        logger.info("Sets processed: %d", stats["sets_processed"])
        logger.info("Cards processed: %d", stats["cards_processed"])
        logger.info("Errors encountered: %d", stats["errors"])

        if stats["runtime_seconds"]:
            runtime_str = str(datetime.timedelta(seconds=int(stats["runtime_seconds"])))
            logger.info("Total runtime: %s", runtime_str)

        if self.scraper:
            js_urls = self.scraper.get_js_required_urls()
            if js_urls:
                logger.info("JavaScript-required URLs: %d", len(js_urls))

        logger.info("=" * 60)


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
        "--no-caching",
        action="store_true",
        default=False,
        help="Disable response caching (default: caching is enabled)",
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=3600,
        help="Cache time-to-live in seconds (default: 3600)",
    )

    # Monitoring options
    parser.add_argument(
        "--no-monitoring",
        action="store_true",
        default=False,
        help="Disable performance monitoring (default: monitoring is enabled)",
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
        enable_caching=not args.no_caching,
        enable_monitoring=not args.no_monitoring,
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
            logger.info("Pipeline completed successfully!")
            return 0
        except Exception as e:
            logger.error("Pipeline failed: %s", e)
            return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
