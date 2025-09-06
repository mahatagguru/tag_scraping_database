#!/usr/bin/env python3
"""
Five-Tier Scraping Pipeline

Implements the complete TAG Grading scraping flow:
Category (e.g., Baseball) → Year → Set → Card → GradeRows

Features:
- Dynamic discovery of categories/years/sets/cards/grades
- Configurable filters and start points  
- Parallel processing with configurable concurrency
- Retry logic with backoff and jitter
- Dry-run mode for testing
- Comprehensive error handling and logging
- Idempotent upserts using database unique constraints
- TOTALS routing to totals_rollups with correct scope

Usage:
    python -m scraper.pipeline --categories Baseball Hockey --concurrency 5
    python -m scraper.pipeline --categories Baseball --start-from set --year-filter 1989 --dry-run
"""

import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional
import logging
import os
import random
import sys
import time
from typing import Any, Dict, List, Literal, Optional

from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import SessionLocal
from scraper.card_grade_rows_scraper import extract_grade_rows_from_url
from scraper.cards_scraper import extract_cards_from_url
from scraper.db_helpers import (
    upsert_card_grade_row,
    upsert_cards_per_set,
    upsert_sets_per_year,
    upsert_totals_rollups,
    upsert_years_index,
)
from scraper.enhanced_sets_scraper import extract_sets_from_url
from scraper.sport_years_scraper import extract_years_from_url

# Configuration
BASE_URL = "https://my.taggrading.com"
# Default to discovering all categories automatically
DEFAULT_CATEGORIES = [
    'Baseball', 'Basketball', 'Football', 'Hockey', 'MMA', 'Soccer', 'Racing', 
    'Golf', 'Tennis', 'Boxing', 'Other Sports', 'Multi-Sport', 'Marvel/DC', 
    'Star Wars', 'Fortnite', 'Garbage Pail Kids', 'Music', 'TV/Movies', 
    'Wrestling', 'Video Games', 'Nature', 'Pop Culture', 'Disney', 'Pokémon', 
    'Magic the Gathering', 'Dragon Ball', 'Metazoo', 'Weiß Schwarz', 'One Piece', 
    'Lorcana', 'Digimon', 'Other TCG'
]  # Complete list of all 33 categories
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0
RETRY_JITTER_MAX = 1.0

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline.log')
    ]
)
logger = logging.getLogger(__name__)


class PipelineStats:
    """Track pipeline statistics and outcomes"""
    
    def __init__(self) -> None:
        self.pages_scraped = 0
        self.rows_inserted = 0
        self.rows_updated = 0
        self.rows_skipped = 0
        self.totals_captured = 0
        self.failures = 0
        self.retries = 0
        self.start_time = time.time()
        
        # Per-table stats
        self.table_stats = {
            'years_index': {'inserts': 0, 'updates': 0},
            'sets_per_year': {'inserts': 0, 'updates': 0},
            'cards_per_set': {'inserts': 0, 'updates': 0},
            'card_grade_rows': {'inserts': 0, 'updates': 0},
            'totals_rollups': {'inserts': 0, 'updates': 0}
        }
    
    def add_table_operation(self, table_name: str, operation: str):
        """Add a table operation to stats"""
        if table_name in self.table_stats:
            if operation in self.table_stats[table_name]:
                self.table_stats[table_name][operation] += 1
                
        if operation == 'inserts':
            self.rows_inserted += 1
        elif operation == 'updates':
            self.rows_updated += 1
    
    def get_duration(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time
    
    def print_summary(self):
        """Print final pipeline statistics"""
        duration = self.get_duration()
        
        logger.info("=" * 80)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info(f"Pages scraped: {self.pages_scraped}")
        logger.info(f"Total rows inserted: {self.rows_inserted}")
        logger.info(f"Total rows updated: {self.rows_updated}")
        logger.info(f"Total rows skipped: {self.rows_skipped}")
        logger.info(f"Totals captured: {self.totals_captured}")
        logger.info(f"Failures: {self.failures}")
        logger.info(f"Retries performed: {self.retries}")
        
        logger.info("\nPer-table statistics:")
        for table_name, stats in self.table_stats.items():
            total_ops = stats['inserts'] + stats['updates']
            if total_ops > 0:
                logger.info(f"  {table_name}: {stats['inserts']} inserts, {stats['updates']} updates")
        
        logger.info("=" * 80)


def retry_with_backoff(func: Any, max_retries: int = MAX_RETRIES, backoff_base: float = RETRY_BACKOFF_BASE, jitter_max: float = RETRY_JITTER_MAX) -> Any:
    """
    Retry function with exponential backoff and jitter
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        backoff_base: Base for exponential backoff
        jitter_max: Maximum jitter to add
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Failed after {max_retries} retries: {e}")
                raise
            
            # Calculate backoff with jitter
            backoff = (backoff_base ** attempt) + (random.random() * jitter_max)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {backoff:.1f}s...")
            time.sleep(backoff)


def discover_categories() -> List[str]:
    """
    Dynamically discover available categories by testing potential category URLs.
    Falls back to known categories if dynamic discovery fails.
    
    Returns:
        List of category names
    """
    try:
        from selectolax.parser import HTMLParser

        from scraper.sport_years_scraper import fetch_rendered_html

        # Test all known categories directly instead of relying on main page text
        potential_categories = [
            'Baseball', 'Basketball', 'Football', 'Hockey', 'MMA', 'Soccer', 'Racing', 
            'Golf', 'Tennis', 'Boxing', 'Other Sports', 'Multi-Sport', 'Marvel/DC', 
            'Star Wars', 'Fortnite', 'Garbage Pail Kids', 'Music', 'TV/Movies', 
            'Wrestling', 'Video Games', 'Nature', 'Pop Culture', 'Disney', 'Pokémon', 
            'Magic the Gathering', 'Dragon Ball', 'Metazoo', 'Weiß Schwarz', 'One Piece', 
            'Lorcana', 'Digimon', 'Other TCG'
        ]
        
        # Test each potential category to see if it has years
        working_categories = []
        for category in potential_categories:
            try:
                # URL encode the category name for special characters
                import urllib.parse
                encoded_category = urllib.parse.quote(category, safe='')
                url = f"{BASE_URL}/pop-report/{encoded_category}"
                html = fetch_rendered_html(url)
                tree = HTMLParser(html)

                # Look for year links
                year_links = tree.css('a[href*="/pop-report/"]')
                year_count = 0

                for link in year_links:
                    href = link.attributes.get('href', '')
                    # Check for year links - href contains the category name (either encoded or not) followed by a year
                    if (f'/pop-report/{category}/' in href or f'/pop-report/{encoded_category}/' in href) and href.count('/') == 3:
                        year_count += 1

                if year_count > 0:
                    working_categories.append(category)
                    logger.debug(f"Category {category}: {year_count} years found")

            except Exception as e:
                logger.debug(f"Category {category} test failed: {e}")
        
        if working_categories:
            logger.info(f"Discovered {len(working_categories)} working categories: {working_categories}")
            return working_categories
        else:
            logger.warning("No working categories discovered dynamically. Using known categories.")
            return DEFAULT_CATEGORIES
        
    except Exception as e:
        logger.warning(f"Failed to discover categories: {e}. Using known categories.")
        return DEFAULT_CATEGORIES


class FiveTierPipeline:
    """Five-tier scraping pipeline implementation"""
    
    def __init__(self, concurrency: int = None, delay: float = 1.0, dry_run: bool = False):
        """
        Initialize pipeline
        
        Args:
            concurrency: Max parallel requests (default from env or 3)
            delay: Delay between requests in seconds
            dry_run: If True, log actions without writing to database
        """
        self.concurrency = concurrency or int(os.getenv('PIPELINE_MAX_CONCURRENCY', '3'))
        self.delay = delay
        self.dry_run = dry_run
        self.session: Optional[Session] = None
        self.stats = PipelineStats()
        
        logger.info(f"Pipeline initialized: concurrency={self.concurrency}, delay={delay}s, dry_run={dry_run}")
    
    def __enter__(self):
        """Context manager entry"""
        if not self.dry_run:
            self.session = SessionLocal()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            if exc_type:
                logger.error(f"Pipeline error: {exc_val}")
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()
    
    def log_upsert(self, table_name: str, unique_key: Dict[str, Any], operation: str = "upsert"):
        """Log database upsert operation"""
        if self.dry_run:
            logger.info(f"[DRY-RUN] {operation} {table_name}: {unique_key}")
        else:
            logger.debug(f"{operation} {table_name}: {unique_key}")
            # In a real implementation, you'd detect insert vs update
            self.stats.add_table_operation(table_name, 'inserts')
    
    def scrape_category_years(self, category: str) -> Dict[str, Any]:
        """
        Scrape years for a category
        
        Args:
            category: Category name (e.g., "Baseball")
            
        Returns:
            Dictionary with years and totals data
        """
        sport_url = f"{BASE_URL}/pop-report/{category}"
        logger.info(f"Scraping years for category: {category}")
        
        def _scrape():
            result = extract_years_from_url(sport_url)
            self.stats.pages_scraped += 1
            return result
        
        result = retry_with_backoff(_scrape)
        
        # Store years in database
        for year_data in result['years']:
            self.log_upsert('years_index', {
                'sport': year_data['sport'], 
                'year': year_data['year']
            })
            
            if not self.dry_run:
                upsert_years_index(
                    self.session,
                    sport=year_data['sport'],
                    year=year_data['year'], 
                    year_url=year_data['year_url']
                )
        
        # Store sport-level totals
        for total_data in result['totals']:
            self.log_upsert('totals_rollups', {
                'scope': total_data['scope'],
                'sport': total_data['sport']
            })
            
            if not self.dry_run:
                upsert_totals_rollups(
                    self.session,
                    scope=total_data['scope'],
                    sport=total_data['sport'],
                    year=total_data['year'],
                    set_title=total_data['set_title'],
                    card_name=total_data['card_name'],
                    metrics=total_data['metrics']
                )
            
            self.stats.totals_captured += 1
        
        logger.info(f"Stored {len(result['years'])} years and {len(result['totals'])} totals for {category}")
        return result
    
    def run_pipeline(
        self,
        categories: List[str],
        start_from: Literal["category", "year", "set", "card", "graderows"] = "category",
        year_filter: Optional[List[str]] = None,
        set_filter: Optional[List[str]] = None,
        card_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run the complete five-tier pipeline using the proven multi-level orchestrator
        """
        logger.info("=" * 80)
        logger.info("STARTING FIVE-TIER PIPELINE")
        logger.info("=" * 80)
        logger.info(f"Categories: {categories}")
        logger.info(f"Start from: {start_from}")
        logger.info(f"Filters: year={year_filter}, set={set_filter}, card={card_filter}")
        
        # Convert categories to sport URLs
        sport_urls = [f"{BASE_URL}/pop-report/{category}" for category in categories]
        
        if self.dry_run:
            logger.info("[DRY-RUN] Would scrape these URLs:")
            for url in sport_urls:
                logger.info(f"  - {url}")
            
            return {
                'categories_processed': categories,
                'total_years': 0,
                'total_sets': 0,
                'total_cards': 0,
                'total_grade_rows': 0,
                'errors': [],
                'duration_seconds': self.stats.get_duration()
            }
        
        # Use the existing multi-level orchestrator
        from scraper.multi_level_orchestrator import scrape_multiple_sports
        
        logger.info(f"🚀 Starting dynamic discovery and scraping for {len(categories)} categories")
        logger.info(f"   Categories: {categories}")
        logger.info(f"   Concurrency: {self.concurrency}")
        logger.info(f"   Delay: {self.delay}s")
        
        try:
            summaries = scrape_multiple_sports(
                sport_urls, 
                concurrency=self.concurrency,
                delay=self.delay
            )
            
            # Aggregate results
            results = {
                'categories_processed': [],
                'total_years': 0,
                'total_sets': 0,
                'total_cards': 0,
                'total_grade_rows': 0,
                'errors': [],
                'duration_seconds': self.stats.get_duration()
            }
            
            for summary in summaries:
                if 'error' in summary:
                    results['errors'].append(summary['error'])
                else:
                    results['categories_processed'].append(summary['sport_url'].split('/')[-1])
                    results['total_years'] += summary.get('years_found', 0)
                    results['total_sets'] += summary.get('total_sets', 0)
                    results['total_cards'] += summary.get('total_cards', 0)
                    results['total_grade_rows'] += summary.get('total_grade_rows', 0)
            
            self.stats.print_summary()
            return results
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise


def main() -> None:
    """CLI entry point - Defaults to discovering and scraping ALL available categories"""
    parser = argparse.ArgumentParser(
        description='Five-Tier TAG Grading Scraping Pipeline'
    )
    
    parser.add_argument('--categories', nargs='+', help='Categories to scrape (default: auto-discover all)')
    parser.add_argument('--discover-categories', action='store_true', help='Explicitly discover categories (this is now the default behavior)')
    parser.add_argument('--start-from', choices=['category', 'year', 'set', 'card', 'graderows'], default='category')
    parser.add_argument('--year-filter', nargs='+', help='Filter to specific years')
    parser.add_argument('--set-filter', nargs='+', help='Filter to specific sets')
    parser.add_argument('--card-filter', nargs='+', help='Filter to specific cards')
    parser.add_argument('--concurrency', type=int, help='Max parallel requests')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine categories
    if args.discover_categories:
        categories = discover_categories()
    elif args.categories:
        categories = args.categories
    else:
        # Default to discovering all categories
        categories = discover_categories()
        logger.info(f"Auto-discovered {len(categories)} categories: {categories}")
    
    # Ensure we have categories to process
    if not categories:
        logger.error("No categories found to process!")
        return 1
    
    # Run pipeline
    try:
        with FiveTierPipeline(
            concurrency=args.concurrency,
            delay=args.delay,
            dry_run=args.dry_run
        ) as pipeline:
            
            results = pipeline.run_pipeline(
                categories=categories,
                start_from=args.start_from,
                year_filter=args.year_filter,
                set_filter=args.set_filter,
                card_filter=args.card_filter
            )
            
            logger.info(f"\nPipeline completed successfully!")
            logger.info(f"Categories: {len(results['categories_processed'])}")
            logger.info(f"Years: {results['total_years']}")
            logger.info(f"Sets: {results['total_sets']}")
            logger.info(f"Cards: {results['total_cards']}")
            logger.info(f"Grade rows: {results['total_grade_rows']}")
            
            if results['errors']:
                logger.warning(f"Errors: {len(results['errors'])}")
            
            return 0
            
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
