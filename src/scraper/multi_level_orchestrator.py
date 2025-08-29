#!/usr/bin/env python3
"""
Multi-Level Scraping Orchestrator

Coordinates the complete scraping flow:
1. Scrape Years index from sport page
2. For each year, scrape Sets from year page  
3. Handle TOTALS at both levels
4. Store data in the new database tables

Supports parallel processing with configurable concurrency.
"""

import sys
import time
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session

# Add project root to path
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import SessionLocal
from scraper.sport_years_scraper import extract_years_from_url
from scraper.enhanced_sets_scraper import extract_sets_from_url
from scraper.cards_scraper import extract_cards_from_url
from scraper.card_grade_rows_scraper import extract_grade_rows_from_url
from scraper.db_helpers import (
    upsert_years_index, upsert_sets_per_year, upsert_totals_rollups, upsert_cards_per_set, upsert_card_grade_row
)


class MultiLevelOrchestrator:
    """Orchestrates multi-level scraping of sport -> years -> sets"""
    
    def __init__(self, concurrency=3, delay_between_requests=1.0):
        """
        Initialize orchestrator.
        
        Args:
            concurrency: Maximum number of parallel requests
            delay_between_requests: Delay in seconds between requests
        """
        self.concurrency = concurrency
        self.delay_between_requests = delay_between_requests
        self.session = None
        
    def __enter__(self):
        """Context manager entry"""
        self.session = SessionLocal()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()
    
    def scrape_sport_years_index(self, sport_url):
        """
        Scrape the years index for a sport.
        
        Args:
            sport_url: Sport index URL (e.g., "https://my.taggrading.com/pop-report/Baseball")
            
        Returns:
            dict: Results from sport years scraper
        """
        print(f"Scraping years index: {sport_url}")
        
        try:
            result = extract_years_from_url(sport_url)
            
            # Validate discovered data
            if not result.get('years'):
                print(f"Warning: No years discovered for {sport_url}")
                return {'years': [], 'totals': []}
            
            print(f"  Discovered {len(result['years'])} years: {[y['year'] for y in result['years']]}")
            
            # Store years in database
            for year_data in result['years']:
                # Validate year data
                if not year_data.get('year') or not year_data.get('year_url'):
                    print(f"    Warning: Skipping invalid year data: {year_data}")
                    continue
                    
                upsert_years_index(
                    self.session,
                    sport=year_data['sport'],
                    year=year_data['year'],
                    year_url=year_data['year_url']
                )
            
            # Store sport-level totals
            for total_data in result['totals']:
                upsert_totals_rollups(
                    self.session,
                    scope=total_data['scope'],
                    sport=total_data['sport'],
                    year=total_data['year'],
                    set_title=total_data['set_title'],
                    metrics=total_data['metrics']
                )
            
            self.session.commit()
            print(f"Stored {len(result['years'])} years and {len(result['totals'])} totals for sport")
            
            return result
            
        except Exception as e:
            print(f"Error scraping sport years: {e}")
            self.session.rollback()
            raise
    
    def scrape_year_sets(self, year_url):
        """
        Scrape sets for a specific year.
        
        Args:
            year_url: Year page URL
            
        Returns:
            dict: Results from sets scraper
        """
        print(f"  Scraping sets: {year_url}")
        
        try:
            result = extract_sets_from_url(year_url)
            
            # Validate discovered data
            if not result.get('sets'):
                print(f"    Warning: No sets discovered for {year_url}")
                return {'sets': [], 'totals': []}
            
            print(f"    Discovered {len(result['sets'])} sets: {[s['set_title'] for s in result['sets']]}")
            
            # Store sets in database
            for set_data in result['sets']:
                # Validate set data
                if not set_data.get('set_title') or not set_data.get('set_urls'):
                    print(f"      Warning: Skipping invalid set data: {set_data}")
                    continue
                    
                upsert_sets_per_year(
                    self.session,
                    sport=set_data['sport'],
                    year=set_data['year'],
                    year_url=set_data['year_url'],
                    set_title=set_data['set_title'],
                    set_urls=set_data['set_urls'],
                    metrics=set_data['metrics']
                )
            
            # Store year-level totals
            for total_data in result['totals']:
                upsert_totals_rollups(
                    self.session,
                    scope=total_data['scope'],
                    sport=total_data['sport'],
                    year=total_data['year'],
                    set_title=total_data['set_title'],
                    card_name=None,
                    metrics=total_data['metrics']
                )
            
            print(f"    Stored {len(result['sets'])} sets and {len(result['totals'])} totals")
            
            return result
            
        except Exception as e:
            print(f"    Error scraping year sets: {e}")
            return {'sets': [], 'totals': []}
    
    def scrape_set_cards(self, set_data):
        """
        Scrape cards for a specific set.
        
        Args:
            set_data: Set data from sets scraper
            
        Returns:
            dict: Results from cards scraper
        """
        if not set_data.get('set_page_url'):
            print(f"      No set page URL for {set_data['set_title']}, skipping cards")
            return {'cards': [], 'totals': []}
        
        print(f"      Scraping cards: {set_data['set_title']}")
        
        try:
            result = extract_cards_from_url(set_data['set_page_url'], set_data['set_title'])
            
            # Validate discovered data
            if not result.get('cards'):
                print(f"        Warning: No cards discovered for {set_data['set_title']}")
                return {'cards': [], 'totals': []}
            
            print(f"        Discovered {len(result['cards'])} cards: {[c['card_name'] for c in result['cards'][:5]]}{'...' if len(result['cards']) > 5 else ''}")
            
            # Store cards in database
            for card_data in result['cards']:
                # Validate card data
                if not card_data.get('card_name') or not card_data.get('card_urls'):
                    print(f"          Warning: Skipping invalid card data: {card_data}")
                    continue
                    
                upsert_cards_per_set(
                    self.session,
                    sport=card_data['sport'],
                    year=card_data['year'],
                    set_title=card_data['set_title'],
                    set_url=card_data['set_url'],
                    card_name=card_data['card_name'],
                    card_urls=card_data['card_urls'],
                    metrics=card_data['metrics']
                )
            
            # Store set-level totals
            for total_data in result['totals']:
                upsert_totals_rollups(
                    self.session,
                    scope=total_data['scope'],
                    sport=total_data['sport'],
                    year=total_data['year'],
                    set_title=total_data['set_title'],
                    card_name=total_data['card_name'],
                    metrics=total_data['metrics']
                )
            
            print(f"        Stored {len(result['cards'])} cards and {len(result['totals'])} totals")
            
            return result
            
        except Exception as e:
            print(f"        Error scraping set cards: {e}")
            return {'cards': [], 'totals': []}
    
    def scrape_card_grade_rows(self, card_data):
        """
        Scrape grade rows for a specific card.
        
        Args:
            card_data: Card data from cards scraper
            
        Returns:
            int: Number of grade rows scraped
        """
        if not card_data.get('card_urls'):
            print(f"          No card URLs for {card_data['card_name']}, skipping grade rows")
            return 0
        
        # Use the first (primary) card URL
        primary_card_url = card_data['card_urls'][0]
        print(f"          Scraping grade rows: {card_data['card_name']}")
        
        try:
            grade_rows = extract_grade_rows_from_url(primary_card_url, card_data['set_title'])
            
            # Store grade rows in database
            for row_data in grade_rows:
                upsert_card_grade_row(
                    self.session,
                    sport=row_data['sport'],
                    year=row_data['year'],
                    set_title=row_data['set_title'],
                    card_name=row_data['card_name'],
                    card_url=row_data['card_url'],
                    cert_number=row_data['cert_number'],
                    rank=row_data.get('rank'),
                    tag_grade=row_data.get('tag_grade'),
                    report_url=row_data.get('report_url'),
                    rank_by_grade=row_data.get('rank_by_grade'),
                    chronology=row_data.get('chronology'),
                    chron_by_grade=row_data.get('chron_by_grade'),
                    completed_date_raw=row_data.get('completed_date_raw'),
                    completed_date_iso=row_data.get('completed_date_iso')
                )
            
            # Log report URL discovery
            report_urls_found = sum(1 for row in grade_rows if row.get('report_url'))
            if report_urls_found > 0:
                print(f"            Stored {len(grade_rows)} grade rows with {report_urls_found} report URLs")
            else:
                print(f"            Stored {len(grade_rows)} grade rows (no report URLs found)")
            return len(grade_rows)
            
        except Exception as e:
            print(f"            Error scraping card grade rows: {e}")
            return 0
    
    def scrape_year_sets_with_delay(self, year_url):
        """Scrape year sets with delay for rate limiting"""
        if self.delay_between_requests > 0:
            time.sleep(self.delay_between_requests)
        return self.scrape_year_sets(year_url)
    
    def scrape_sport_complete(self, sport_url):
        """
        Complete scraping flow for a sport: years index + all year sets.
        
        Args:
            sport_url: Sport index URL
            
        Returns:
            dict: Complete results summary
        """
        print(f"\n{'='*60}")
        print(f"Starting complete scrape for: {sport_url}")
        print('='*60)
        
        start_time = time.time()
        
        # Step 1: Scrape years index
        years_result = self.scrape_sport_years_index(sport_url)
        year_urls = [year_data['year_url'] for year_data in years_result['years']]
        
        print(f"\nFound {len(year_urls)} years to scrape")
        
        # Step 2: Scrape all year sets (with controlled parallelism)
        all_sets = []
        all_year_totals = []
        
        if self.concurrency > 1:
            print(f"Using parallel processing with concurrency={self.concurrency}")
            
            with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
                # Submit all year scraping tasks
                future_to_url = {
                    executor.submit(self.scrape_year_sets_with_delay, url): url 
                    for url in year_urls
                }
                
                # Process completed tasks
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        result = future.result()
                        all_sets.extend(result['sets'])
                        all_year_totals.extend(result['totals'])
                    except Exception as e:
                        print(f"    Error processing {url}: {e}")
        else:
            print("Using sequential processing")
            for url in year_urls:
                result = self.scrape_year_sets_with_delay(url)
                all_sets.extend(result['sets'])
                all_year_totals.extend(result['totals'])
        
        # Step 3: Scrape all set cards (with controlled parallelism)
        print(f"\n  Starting card scraping for {len(all_sets)} sets...")
        all_cards = []
        all_set_totals = []
        
        if self.concurrency > 1:
            print(f"Using parallel processing with concurrency={self.concurrency}")
            
            with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
                # Submit all set card scraping tasks
                future_to_set = {
                    executor.submit(self.scrape_set_cards, set_data): set_data 
                    for set_data in all_sets
                }
                
                # Process completed tasks
                for future in as_completed(future_to_set):
                    set_data = future_to_set[future]
                    try:
                        result = future.result()
                        all_cards.extend(result['cards'])
                        all_set_totals.extend(result['totals'])
                    except Exception as e:
                        print(f"      Error processing set {set_data['set_title']}: {e}")
        else:
            print("Using sequential processing")
            for set_data in all_sets:
                result = self.scrape_set_cards(set_data)
                all_cards.extend(result['cards'])
                all_set_totals.extend(result['totals'])
        
        # Step 4: Scrape all card grade rows (with controlled parallelism)
        print(f"\n  Starting grade rows scraping for {len(all_cards)} cards...")
        total_grade_rows = 0
        
        if self.concurrency > 1:
            print(f"Using parallel processing with concurrency={self.concurrency}")
            
            with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
                # Submit all card grade row scraping tasks
                future_to_card = {
                    executor.submit(self.scrape_card_grade_rows, card_data): card_data 
                    for card_data in all_cards
                }
                
                # Process completed tasks
                for future in as_completed(future_to_card):
                    card_data = future_to_card[future]
                    try:
                        grade_rows_count = future.result()
                        total_grade_rows += grade_rows_count
                    except Exception as e:
                        print(f"        Error processing card {card_data['card_name']}: {e}")
        else:
            print("Using sequential processing")
            for card_data in all_cards:
                grade_rows_count = self.scrape_card_grade_rows(card_data)
                total_grade_rows += grade_rows_count
        
        # Commit all changes at once
        self.session.commit()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate pages scraped
        pages_scraped = (
            1 +  # Sport index page
            len(years_result['years']) +  # Year pages
            len(all_sets) +  # Set pages
            len(all_cards)   # Card pages
        )
        
        # Summary
        summary = {
            'sport_url': sport_url,
            'years_found': len(years_result['years']),
            'sport_totals': len(years_result['totals']),
            'total_sets': len(all_sets),
            'year_totals': len(all_year_totals),
            'total_cards': len(all_cards),
            'set_totals': len(all_set_totals),
            'total_grade_rows': total_grade_rows,
            'duration_seconds': duration,
            'pages_scraped': pages_scraped
        }
        
        print(f"\n{'='*60}")
        print("SCRAPING COMPLETE")
        print('='*60)
        print(f"Sport: {sport_url}")
        print(f"Years found: {summary['years_found']}")
        print(f"Total sets: {summary['total_sets']}")
        print(f"Total cards: {summary['total_cards']}")
        print(f"Total grade rows: {summary['total_grade_rows']}")
        print(f"Sport-level totals: {summary['sport_totals']}")
        print(f"Year-level totals: {summary['year_totals']}")
        print(f"Set-level totals: {summary['set_totals']}")
        print(f"Pages scraped: {summary['pages_scraped']}")
        print(f"Duration: {duration:.1f} seconds")
        print('='*60)
        
        return summary


def scrape_sport(sport_url, concurrency=3, delay=1.0):
    """
    Convenience function to scrape a single sport completely.
    
    Args:
        sport_url: Sport index URL
        concurrency: Max parallel requests
        delay: Delay between requests
        
    Returns:
        dict: Scraping summary
    """
    with MultiLevelOrchestrator(concurrency=concurrency, delay_between_requests=delay) as orchestrator:
        return orchestrator.scrape_sport_complete(sport_url)


def scrape_multiple_sports(sport_urls, concurrency=3, delay=1.0):
    """
    Scrape multiple sports sequentially.
    
    Args:
        sport_urls: List of sport index URLs
        concurrency: Max parallel requests per sport
        delay: Delay between requests
        
    Returns:
        list: List of scraping summaries
    """
    summaries = []
    
    for i, sport_url in enumerate(sport_urls):
        print(f"\n\nSport {i+1}/{len(sport_urls)}: {sport_url}")
        
        try:
            summary = scrape_sport(sport_url, concurrency=concurrency, delay=delay)
            summaries.append(summary)
        except Exception as e:
            print(f"Error scraping sport {sport_url}: {e}")
            summaries.append({
                'sport_url': sport_url,
                'error': str(e)
            })
    
    return summaries


def main():
    """Test the multi-level orchestrator"""
    # Test URLs
    sport_urls = [
        "https://my.taggrading.com/pop-report/Baseball",
        "https://my.taggrading.com/pop-report/Hockey"
    ]
    
    print("Testing Multi-Level Orchestrator")
    print(f"Sports to scrape: {len(sport_urls)}")
    
    summaries = scrape_multiple_sports(
        sport_urls, 
        concurrency=3,  # Moderate parallelism
        delay=1.0       # 1 second delay between requests
    )
    
    print(f"\n\n{'='*80}")
    print("FINAL SUMMARY")
    print('='*80)
    
    total_years = 0
    total_sets = 0
    
    for summary in summaries:
        if 'error' in summary:
            print(f"FAILED: {summary['sport_url']} - {summary['error']}")
        else:
            print(f"SUCCESS: {summary['sport_url']}")
            print(f"  Years: {summary['years_found']}")
            print(f"  Sets: {summary['total_sets']}")
            print(f"  Duration: {summary['duration_seconds']:.1f}s")
            total_years += summary['years_found']
            total_sets += summary['total_sets']
    
    print(f"\nTOTAL ACROSS ALL SPORTS:")
    print(f"  Years: {total_years}")
    print(f"  Sets: {total_sets}")
    print('='*80)


if __name__ == "__main__":
    main()
