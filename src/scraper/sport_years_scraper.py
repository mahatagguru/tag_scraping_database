#!/usr/bin/env python3
"""
Sport Years Index Scraper

Scrapes the "Sets per Year" table from sport index pages like:
- https://my.taggrading.com/pop-report/Baseball
- https://my.taggrading.com/pop-report/Hockey

Extracts year labels and URLs while handling TOTALS rows separately.
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
        print(
            "Playwright is not installed. Please run: pip install playwright && python3 -m playwright install"
        )
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        html = page.content()
        browser.close()
        return html


def normalize_text(text: Optional[str]) -> str:
    """Normalize text by trimming and collapsing whitespace"""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())


def extract_metrics_from_row(row: Any) -> Dict[str, Any]:
    """Extract numeric metrics from table row cells (excluding first cell)"""
    metrics: Dict[str, Any] = {}
    cells = row.css("td.MuiTableCell-root")

    if len(cells) < 2:
        return metrics

    # Skip first cell (title cell), extract from remaining cells
    metric_cells = cells[1:]

    # Common column patterns we expect to find
    metric_names = ["num_sets", "total_items", "total_graded"]

    for i, cell in enumerate(metric_cells):
        text = normalize_text(cell.text())

        # Try to parse as integer
        if text and text.replace(",", "").replace("-", "").isdigit():
            value = int(text.replace(",", "").replace("-", "0"))

            # Use known metric names if available, otherwise use index
            if i < len(metric_names):
                metrics[metric_names[i]] = value
            else:
                metrics[f"metric_{i}"] = value
        elif text and text != "-":
            # Store non-numeric values as strings
            if i < len(metric_names):
                metrics[metric_names[i]] = text
            else:
                metrics[f"metric_{i}"] = text

    return metrics


def extract_years_index(html: str, sport: str) -> Dict[str, Any]:
    """
    Extract years index from sport page HTML.

    Args:
        html: Raw HTML content
        sport: Sport name (e.g., "Baseball", "Hockey")

    Returns:
        dict with 'years' and 'totals' keys:
        {
            'years': [
                {
                    'sport': 'Baseball',
                    'year': '1989',
                    'year_url': 'https://my.taggrading.com/pop-report/Baseball/1989',
                    'row_index': 0
                }
            ],
            'totals': [
                {
                    'scope': 'sport',
                    'sport': 'Baseball',
                    'year': None,
                    'set_title': None,
                    'metrics': {'num_sets': 4405, 'total_items': 9708, 'total_graded': 46291}
                }
            ]
        }
    """
    tree = HTMLParser(html)
    years = []
    totals = []

    # Find table body rows
    rows = tree.css("tbody tr.MuiTableRow-root")

    for row_index, row in enumerate(rows):
        # Get the first cell (title cell)
        title_cell = row.css_first("td")
        if not title_cell:
            continue

        # Extract title text and normalize
        title_text = normalize_text(title_cell.text())

        # Check if this is a TOTALS row
        if title_text.upper() == "TOTALS":
            # Extract metrics from this TOTALS row
            metrics = extract_metrics_from_row(row)

            totals.append(
                {
                    "scope": "sport",
                    "sport": sport,
                    "year": None,
                    "set_title": None,
                    "metrics": metrics,
                }
            )
            continue

        # Validate year format (should be 4-digit year)
        if not re.match(r"^\d{4}$", title_text):
            print(f"Skipping non-year row: '{title_text}'")
            continue

        # Extract URL from first anchor in title cell
        year_url = None
        anchors = title_cell.css("a[href]")

        for anchor in anchors:
            href = anchor.attributes.get("href", "")
            # Filter out non-destinations
            if href and not href.startswith("#") and not href.startswith("javascript:"):
                # Convert to absolute URL
                year_url = urljoin(BASE_URL, href)
                break  # Use first valid URL as primary

        if not year_url:
            print(f"Warning: No URL found for year {title_text}")
            continue

        years.append(
            {
                "sport": sport,
                "year": title_text,
                "year_url": year_url,
                "row_index": row_index,
            }
        )

    return {"years": years, "totals": totals}


def extract_years_from_url(url: str) -> Dict[str, Any]:
    """
    Extract years index from a sport URL.

    Args:
        url: Sport index URL (e.g., "https://my.taggrading.com/pop-report/Baseball")

    Returns:
        dict with 'years' and 'totals' keys
    """
    # Extract sport name from URL
    sport = url.rstrip("/").split("/")[-1]

    print(f"Fetching years index for sport: {sport}")
    html = fetch_rendered_html(url)

    return extract_years_index(html, sport)


def main() -> None:
    """Test the years index scraper"""
    # Test URLs
    test_urls = [
        "https://my.taggrading.com/pop-report/Baseball",
        "https://my.taggrading.com/pop-report/Hockey",
    ]

    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing Years Index Scraper: {url}")
        print("=" * 60)

        try:
            result = extract_years_from_url(url)

            print(f"\nFound {len(result['years'])} years:")
            for year_data in result["years"]:
                print(f"  {year_data['year']} -> {year_data['year_url']}")

            print(f"\nFound {len(result['totals'])} totals:")
            for total_data in result["totals"]:
                print(f"  {total_data['scope']} scope: {total_data['metrics']}")

        except Exception as e:
            print(f"Error scraping {url}: {e}")


if __name__ == "__main__":
    main()
