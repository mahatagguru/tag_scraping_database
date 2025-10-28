#!/usr/bin/env python3
"""
Example script to run the new high-performance async scraping pipeline.
"""

import asyncio
import sys

from src.scraper.async_pipeline import AsyncPipelineConfig, AsyncScrapingPipeline


async def main():
    """Run the async pipeline with optimized settings."""
    print("🚀 Starting high-performance async TAG Grading scraper...")

    # Configure the pipeline for optimal performance
    config = AsyncPipelineConfig(
        max_concurrent_requests=15,  # High concurrency for fast scraping
        max_concurrent_db_operations=8,  # Multiple DB operations
        rate_limit=0.5,  # Faster rate limit
        batch_size=200,  # Large batches for efficiency
        enable_caching=True,  # Enable intelligent caching
        enable_monitoring=True,  # Enable performance monitoring
        cache_ttl=3600,  # 1 hour cache TTL
        db_pool_size=25,  # Large connection pool
        dry_run=False,  # Actually run the scraper
        # Uncomment to filter specific sports
        # year_filter=['2023', '2024'],  # Filter to recent years
        # set_filter=['Topps', 'Panini'], # Filter to specific sets
    )

    # Run the pipeline
    async with AsyncScrapingPipeline(config) as pipeline:
        try:
            # Run for all sports or specify specific ones
            # stats = await pipeline.run_pipeline(['Baseball', 'Hockey'])
            stats = await pipeline.run_pipeline()  # All sports

            print("\n🎉 Pipeline completed successfully!")
            print("📊 Final Statistics:")
            print(f"  Categories processed: {stats['categories_processed']}")
            print(f"  Years processed: {stats['years_processed']}")
            print(f"  Sets processed: {stats['sets_processed']}")
            print(f"  Cards processed: {stats['cards_processed']}")
            print(f"  Errors encountered: {stats['errors']}")

            if stats["runtime_seconds"]:
                runtime_minutes = stats["runtime_seconds"] / 60
                print(f"  Total runtime: {runtime_minutes:.2f} minutes")

            return 0

        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            import traceback

            traceback.print_exc()
            return 1


if __name__ == "__main__":
    # Run the async pipeline
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
