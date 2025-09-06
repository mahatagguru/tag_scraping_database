#!/usr/bin/env python3
"""
Enhanced Sets Scraper

Scrapes sets tables from year pages like:
- https://my.taggrading.com/pop-report/Baseball/1989
- https://my.taggrading.com/pop-report/Hockey/1989

Extracts set titles, URLs, and metrics while handling TOTALS rows separately.
"""

import re
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

BASE_URL = "https://my.taggrading.com"


def fetch_rendered_html(url: str) -> str:
    """Fetch rendered HTML using Playwright for dynamic content"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is not installed. Please run: pip install playwright && python3 -m playwright install")
        sys.exit(1)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        html: str = page.content()
        browser.close()
        return html


def normalize_text(text: Optional[str]) -> str:
    """Normalize text by trimming and collapsing whitespace"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())


def extract_metrics_from_row(row: Any) -> Dict[str, Any]:
    """Extract numeric metrics from table row cells (excluding first cell)"""
    metrics: Dict[str, Any] = {}
    cells = row.css('td.MuiTableCell-root')
    
    if len(cells) < 2:
        return metrics
    
    # Skip first cell (title cell), extract from remaining cells
    metric_cells = cells[1:]
    
    # Try to extract column headers from table head for better metric names
    table = row.parent
    if table:
        header_rows = table.css('thead tr')
        grade_names = []
        
        for header_row in header_rows:
            header_cells = header_row.css('th')
            if len(header_cells) > 1:  # Skip first header (title column)
                for i, header_cell in enumerate(header_cells[1:]):
                    header_text = normalize_text(header_cell.text())
                    if header_text and header_text not in ['Grade']:  # Skip generic headers
                        grade_names.append(header_text)
    
    # Extract metrics from cells
    for i, cell in enumerate(metric_cells):
        text = normalize_text(cell.text())
        
        # Try to parse as integer
        if text and text.replace(',', '').replace('-', '').isdigit():
            value = int(text.replace(',', '').replace('-', '0'))
            
            # Use grade names if available, otherwise use generic names
            if i < len(grade_names) and grade_names[i]:
                key = f"grade_{grade_names[i]}"
            else:
                # Common grade patterns
                if i == len(metric_cells) - 1:  # Last cell is usually total
                    key = 'total'
                else:
                    key = f'grade_{i}'
            
            metrics[key] = value
        elif text and text != '-':
            # Store non-numeric values as strings
            if i < len(grade_names) and grade_names[i]:
                key = f"grade_{grade_names[i]}"
            else:
                key = f'grade_{i}'
            metrics[key] = text
    
    return metrics


def extract_set_urls_from_cell(title_cell: Any) -> List[str]:
    """Extract all URLs from the title cell"""
    set_urls: List[str] = []
    anchors = title_cell.css('a[href]')
    
    for anchor in anchors:
        href = anchor.attributes.get('href', '') if anchor.attributes else ''
        # Filter out non-destinations: href that are empty, #, javascript:*
        if href and not href.startswith('#') and not href.startswith('javascript:'):
            # Convert to absolute URL
            absolute_url = urljoin(BASE_URL, href)
            set_urls.append(absolute_url)
    
    # De-duplicate while preserving order
    seen_urls = set()
    unique_urls = []
    for url in set_urls:
        if url not in seen_urls:
            seen_urls.add(url)
            unique_urls.append(url)
    
    return unique_urls


def extract_sets_from_year_page(html: str, sport: str, year: str, year_url: str) -> Dict[str, Any]:
    """
    Extract sets from year page HTML.
    
    Args:
        html: Raw HTML content
        sport: Sport name (e.g., "Baseball")
        year: Year string (e.g., "1989")
        year_url: Year page URL
        
    Returns:
        dict with 'sets' and 'totals' keys:
        {
            'sets': [
                {
                    'sport': 'Baseball',
                    'year': '1989',
                    'year_url': '...',
                    'set_title': 'Classic Light Blue',
                    'set_urls': ['https://...'],
                    'set_page_url': 'https://...',  # Main set page URL for card scraping
                    'metrics': {'grade_10': 1, 'total': 15, ...}
                }
            ],
            'totals': [
                {
                    'scope': 'year',
                    'sport': 'Baseball',
                    'year': '1989',
                    'set_title': None,
                    'metrics': {'total': 592, ...}
                }
            ]
        }
    """
    tree = HTMLParser(html)
    sets = []
    totals = []
    
    # Find table body rows
    rows = tree.css('tbody tr.MuiTableRow-root')
    
    for row in rows:
        # Get the first cell (title cell)
        title_cell = row.css_first('td')
        if not title_cell:
            continue
            
        # Extract title text and normalize
        set_title = normalize_text(title_cell.text())
        
        if not set_title:
            continue
            
        # Check if this is a TOTALS row
        if set_title.upper() == 'TOTALS':
            # Extract metrics from this TOTALS row
            metrics = extract_metrics_from_row(row)
            
            totals.append({
                'scope': 'year',
                'sport': sport,
                'year': year,
                'set_title': None,
                'metrics': metrics
            })
            continue
        
        # Extract URLs from title cell
        set_urls = extract_set_urls_from_cell(title_cell)
        
        # Determine the main set page URL for card scraping
        # Usually the first URL is the main set page
        set_page_url = set_urls[0] if set_urls else None
        
        # Extract metrics from remaining cells
        metrics = extract_metrics_from_row(row)
        
        sets.append({
            'sport': sport,
            'year': year,
            'year_url': year_url,
            'set_title': set_title,
            'set_urls': set_urls,
            'set_page_url': set_page_url,
            'metrics': metrics
        })
    
    return {
        'sets': sets,
        'totals': totals
    }


def extract_sets_from_url(year_url: str) -> Dict[str, Any]:
    """
    Extract sets from a year URL.
    
    Args:
        year_url: Year page URL (e.g., "https://my.taggrading.com/pop-report/Baseball/1989")
        
    Returns:
        dict with 'sets' and 'totals' keys
    """
    # Extract sport and year from URL
    url_parts = year_url.rstrip('/').split('/')
    if len(url_parts) < 2:
        raise ValueError(f"Invalid year URL format: {year_url}")
    
    year = url_parts[-1]
    sport = url_parts[-2]
    
    print(f"Fetching sets for {sport} {year}")
    html = fetch_rendered_html(year_url)
    
    return extract_sets_from_year_page(html, sport, year, year_url)


def main() -> None:
    """Test the enhanced sets scraper"""
    # Test URLs
    test_urls = [
        "https://my.taggrading.com/pop-report/Baseball/1989",
        "https://my.taggrading.com/pop-report/Hockey/1989"
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing Enhanced Sets Scraper: {url}")
        print('='*60)
        
        try:
            result = extract_sets_from_url(url)
            
            print(f"\nFound {len(result['sets'])} sets:")
            for i, set_data in enumerate(result['sets'][:5]):  # Show first 5
                print(f"  {i+1}. {set_data['set_title']}")
                print(f"     URLs: {set_data['set_urls']}")
                print(f"     Metrics: {dict(list(set_data['metrics'].items())[:3])}...")  # Show first 3 metrics
                print()
            
            if len(result['sets']) > 5:
                print(f"  ... and {len(result['sets']) - 5} more sets")
            
            print(f"\nFound {len(result['totals'])} totals:")
            for total_data in result['totals']:
                print(f"  {total_data['scope']} scope for {total_data['sport']} {total_data['year']}: {total_data['metrics']}")
                
        except Exception as e:
            print(f"Error scraping {url}: {e}")


if __name__ == "__main__":
    main()
