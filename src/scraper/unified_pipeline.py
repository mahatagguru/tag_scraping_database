#!/usr/bin/env python3
"""
Unified TAG Grading Scraper Pipeline
Consolidates all scraping functionality into a single, optimized pipeline with:
- Dynamic discovery of all categories, years, sets, and cards
- Comprehensive error handling and retry logic
- Database audit logging for all operations
- Support for multiple concurrent runners
- Progress tracking and reporting
- Graceful failure handling
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import os
import sys
import threading
import time
import traceback
from typing import Any, Dict, List, Optional, Tuple

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from db import SessionLocal
from models import AuditLog
from scraper.db_helpers import (
    upsert_card_grade_row,
    upsert_cards_per_set,
    upsert_sets_per_year,
    upsert_totals_rollups,
    upsert_years_index,
)
from scraper.multi_level_orchestrator import MultiLevelOrchestrator
from scraper.pipeline import discover_categories

# Configuration
BASE_URL = "https://my.taggrading.com"
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0
RETRY_JITTER_MAX = 1.0

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('unified_pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PipelineConfig:
    """Configuration for the unified pipeline"""
    concurrency: int = 3
    delay: float = 1.0
    max_retries: int = 3
    retry_backoff: float = 2.0
    dry_run: bool = False
    start_from: str = "category"
    year_filter: Optional[List[str]] = None
    set_filter: Optional[List[str]] = None
    card_filter: Optional[List[str]] = None
    runner_id: Optional[str] = None
    log_level: str = "INFO"

@dataclass
class PipelineStats:
    """Comprehensive pipeline statistics"""
    start_time: float
    categories_processed: int = 0
    years_discovered: int = 0
    sets_discovered: int = 0
    cards_discovered: int = 0
    grade_rows_discovered: int = 0
    totals_captured: int = 0
    errors_encountered: int = 0
    retries_performed: int = 0
    pages_scraped: int = 0
    
    def get_duration(self) -> float:
        return time.time() - self.start_time
    
    def print_summary(self):
        duration = self.get_duration()
        logger.info("=" * 80)
        logger.info("UNIFIED PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info(f"Categories processed: {self.categories_processed}")
        logger.info(f"Years discovered: {self.years_discovered}")
        logger.info(f"Sets discovered: {self.sets_discovered}")
        logger.info(f"Cards discovered: {self.cards_discovered}")
        logger.info(f"Grade rows discovered: {self.grade_rows_discovered}")
        logger.info(f"Totals captured: {self.totals_captured}")
        logger.info(f"Pages scraped: {self.pages_scraped}")
        logger.info(f"Errors encountered: {self.errors_encountered}")
        logger.info(f"Retries performed: {self.retries_performed}")
        logger.info(f"Throughput: {self.pages_scraped/duration:.1f} pages/second")
        logger.info("=" * 80)

class AuditLogger:
    """Handles database audit logging for all pipeline operations"""
    
    def __init__(self, session: Session, runner_id: Optional[str] = None):
        self.session = session
        self.runner_id = runner_id or f"runner_{threading.get_ident()}"
    
    def log_operation(self, level: str, message: str, context: Optional[Dict] = None):
        """Log an operation to the audit log table"""
        try:
            audit_entry = AuditLog(
                level=level,
                message=message,
                context={
                    'runner_id': self.runner_id,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    **(context or {})
                }
            )
            self.session.add(audit_entry)
            self.session.flush()
        except Exception as e:
            logger.error(f"Failed to log to audit table: {e}")
    
    def log_discovery(self, entity_type: str, count: int, details: Dict):
        """Log discovery operations"""
        self.log_operation(
            level="INFO",
            message=f"Discovered {count} {entity_type}",
            context={
                'operation': 'discovery',
                'entity_type': entity_type,
                'count': count,
                'details': details
            }
        )
    
    def log_error(self, operation: str, error: str, context: Optional[Dict] = None):
        """Log error operations"""
        self.log_operation(
            level="ERROR",
            message=f"Error in {operation}: {error}",
            context={
                'operation': operation,
                'error': error,
                **(context or {})
            }
        )
    
    def log_success(self, operation: str, details: Dict):
        """Log successful operations"""
        self.log_operation(
            level="INFO",
            message=f"Successfully completed {operation}",
            context={
                'operation': operation,
                'details': details
            }
        )

class UnifiedPipeline:
    """Unified pipeline that consolidates all scraping functionality"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.stats = PipelineStats(start_time=time.time())
        self.session: Optional[Session] = None
        self.audit_logger: Optional[AuditLogger] = None
        self.lock = threading.Lock()
        
        # Set log level
        logging.getLogger().setLevel(getattr(logging, config.log_level.upper()))
        
        logger.info(f"Unified pipeline initialized: {config}")
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        if self.dry_run:
            yield None
        else:
            session = SessionLocal()
            try:
                self.session = session
                self.audit_logger = AuditLogger(session, self.config.runner_id)
                yield session
            finally:
                if session:
                    session.close()
                    self.session = None
                    self.audit_logger = None
    
    def retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff and jitter"""
        for attempt in range(self.config.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.config.max_retries:
                    logger.error(f"Failed after {self.config.max_retries} retries: {e}")
                    if self.audit_logger:
                        self.audit_logger.log_error("retry_with_backoff", str(e), {
                            'function': func.__name__,
                            'attempts': attempt + 1,
                            'error': str(e)
                        })
                    raise
                
                # Calculate backoff with jitter
                backoff = self.config.retry_backoff ** attempt
                jitter = (time.time() % 1000) / 1000 * self.config.retry_backoff
                sleep_time = backoff + jitter
                
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time:.2f}s")
                if self.audit_logger:
                    self.audit_logger.log_error("retry_with_backoff", str(e), {
                        'function': func.__name__,
                        'attempt': attempt + 1,
                        'retry_delay': sleep_time
                    })
                
                time.sleep(sleep_time)
                self.stats.retries_performed += 1
    
    def discover_and_scrape_categories(self) -> List[str]:
        """Discover all available categories and scrape them"""
        logger.info("🔍 Starting category discovery...")
        
        try:
            categories = self.retry_with_backoff(discover_categories)
            logger.info(f"✅ Discovered {len(categories)} categories: {categories}")
            
            if self.audit_logger:
                self.audit_logger.log_discovery("categories", len(categories), {
                    'categories': categories
                })
            
            return categories
            
        except Exception as e:
            logger.error(f"❌ Category discovery failed: {e}")
            if self.audit_logger:
                self.audit_logger.log_error("category_discovery", str(e))
            raise
    
    def scrape_sport_complete(self, sport_url: str) -> Dict[str, Any]:
        """Scrape a complete sport using the multi-level orchestrator"""
        sport_name = sport_url.split('/')[-1]
        logger.info(f"🚀 Starting complete scrape for {sport_name}")
        
        try:
            with MultiLevelOrchestrator(
                concurrency=self.config.concurrency,
                delay_between_requests=self.config.delay
            ) as orchestrator:
                result = orchestrator.scrape_sport_complete(sport_url)
                
                # Update stats
                with self.lock:
                    self.stats.years_discovered += result.get('years_found', 0)
                    self.stats.sets_discovered += result.get('total_sets', 0)
                    self.stats.cards_discovered += result.get('total_cards', 0)
                    self.stats.grade_rows_discovered += result.get('total_grade_rows', 0)
                    self.stats.totals_captured += result.get('total_totals', 0)
                    self.stats.pages_scraped += result.get('pages_scraped', 0)
                
                if self.audit_logger:
                    self.audit_logger.log_success("sport_scrape", {
                        'sport': sport_name,
                        'years': result.get('years_found', 0),
                        'sets': result.get('total_sets', 0),
                        'cards': result.get('total_cards', 0),
                        'grade_rows': result.get('total_grade_rows', 0)
                    })
                
                logger.info(f"✅ Completed {sport_name}: {result}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to scrape {sport_name}: {e}")
            if self.audit_logger:
                self.audit_logger.log_error("sport_scrape", str(e), {
                    'sport': sport_name,
                    'sport_url': sport_url
                })
            
            with self.lock:
                self.stats.errors_encountered += 1
            
            return {
                'sport': sport_name,
                'error': str(e),
                'years_found': 0,
                'total_sets': 0,
                'total_cards': 0,
                'total_grade_rows': 0,
                'total_totals': 0,
                'pages_scraped': 0
            }
    
    def run_pipeline(self) -> Dict[str, Any]:
        """Run the complete unified pipeline"""
        logger.info("🚀 Starting unified TAG Grading pipeline...")
        logger.info(f"Configuration: {self.config}")
        
        start_time = time.time()
        
        try:
            # Discover categories
            categories = self.discover_and_scrape_categories()
            self.stats.categories_processed = len(categories)
            
            if not categories:
                raise ValueError("No categories discovered")
            
            # Build sport URLs
            sport_urls = [f"{BASE_URL}/pop-report/{category}" for category in categories]
            logger.info(f"📋 Processing {len(sport_urls)} sport URLs")
            
            # Scrape each sport
            results = []
            errors = []
            
            if self.config.concurrency > 1:
                # Use thread pool for concurrent processing
                logger.info(f"🔄 Using {self.config.concurrency} concurrent workers")
                with ThreadPoolExecutor(max_workers=self.config.concurrency) as executor:
                    future_to_sport = {
                        executor.submit(self.scrape_sport_complete, sport_url): sport_url
                        for sport_url in sport_urls
                    }
                    
                    for future in as_completed(future_to_sport):
                        sport_url = future_to_sport[future]
                        try:
                            result = future.result()
                            results.append(result)
                            if 'error' in result:
                                errors.append(result['error'])
                        except Exception as e:
                            error_result = {
                                'sport': sport_url.split('/')[-1],
                                'error': str(e),
                                'years_found': 0,
                                'total_sets': 0,
                                'total_cards': 0,
                                'total_grade_rows': 0,
                                'total_totals': 0,
                                'pages_scraped': 0
                            }
                            results.append(error_result)
                            errors.append(str(e))
                            
                            with self.lock:
                                self.stats.errors_encountered += 1
            else:
                # Sequential processing
                logger.info("🔄 Using sequential processing")
                for sport_url in sport_urls:
                    result = self.scrape_sport_complete(sport_url)
                    results.append(result)
                    if 'error' in result:
                        errors.append(result['error'])
            
            # Compile final results
            final_results = {
                'categories_processed': self.stats.categories_processed,
                'total_years': self.stats.years_discovered,
                'total_sets': self.stats.sets_discovered,
                'total_cards': self.stats.cards_discovered,
                'total_grade_rows': self.stats.grade_rows_discovered,
                'total_totals': self.stats.totals_captured,
                'pages_scraped': self.stats.pages_scraped,
                'errors': errors,
                'error_count': len(errors),
                'duration_seconds': time.time() - start_time,
                'runner_id': self.config.runner_id,
                'config': {
                    'concurrency': self.config.concurrency,
                    'delay': self.config.delay,
                    'max_retries': self.config.max_retries
                }
            }
            
            # Log final results
            if self.audit_logger:
                self.audit_logger.log_success("pipeline_completion", final_results)
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Pipeline execution failed: {e}")
            if self.audit_logger:
                self.audit_logger.log_error("pipeline_execution", str(e), {
                    'traceback': traceback.format_exc()
                })
            
            with self.lock:
                self.stats.errors_encountered += 1
            
            return {
                'error': str(e),
                'traceback': traceback.format_exc(),
                'duration_seconds': time.time() - start_time,
                'runner_id': self.config.runner_id
            }

def main():
    """Main entry point for the unified pipeline"""
    parser = argparse.ArgumentParser(
        description='Unified TAG Grading Scraper Pipeline - Single command for complete scraping'
    )
    
    # Pipeline configuration
    parser.add_argument('--concurrency', type=int, default=3, 
                       help='Number of concurrent workers (default: 3)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum retry attempts (default: 3)')
    parser.add_argument('--retry-backoff', type=float, default=2.0,
                       help='Retry backoff multiplier (default: 2.0)')
    
    # Execution options
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run mode (no database writes)')
    parser.add_argument('--start-from', choices=['category', 'year', 'set', 'card', 'graderows'],
                       default='category', help='Start scraping from this level (default: category)')
    parser.add_argument('--year-filter', nargs='+', help='Filter to specific years')
    parser.add_argument('--set-filter', nargs='+', help='Filter to specific sets')
    parser.add_argument('--card-filter', nargs='+', help='Filter to specific cards')
    
    # Runner identification
    parser.add_argument('--runner-id', help='Unique identifier for this pipeline runner')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = PipelineConfig(
        concurrency=args.concurrency,
        delay=args.delay,
        max_retries=args.max_retries,
        retry_backoff=args.retry_backoff,
        dry_run=args.dry_run,
        start_from=args.start_from,
        year_filter=args.year_filter,
        set_filter=args.set_filter,
        card_filter=args.card_filter,
        runner_id=args.runner_id or f"runner_{os.getpid()}_{int(time.time())}",
        log_level=args.log_level
    )
    
    # Run pipeline
    try:
        pipeline = UnifiedPipeline(config)
        
        with pipeline.get_session():
            results = pipeline.run_pipeline()
            
            # Print results
            if 'error' in results:
                logger.error(f"Pipeline failed: {results['error']}")
                if 'traceback' in results:
                    logger.error(f"Traceback: {results['traceback']}")
                return 1
            else:
                logger.info("🎉 Pipeline completed successfully!")
                logger.info(f"Results: {results}")
                
                # Print summary
                pipeline.stats.print_summary()
                
                return 0
                
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
