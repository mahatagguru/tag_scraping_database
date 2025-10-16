#!/usr/bin/env python3
"""
Cards Scraper

Scrapes cards tables from set pages like:
- https://my.taggrading.com/pop-report/Baseball/1989/Donruss
- https://my.taggrading.com/pop-report/Hockey/1989/Topps

Extracts card names, URLs, and metrics while handling TOTALS rows separately.
This implements the third level of the scraping pipeline: Sport → Year → Set → Cards.
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
        html: str = page.content()
        browser.close()
        return html


def normalize_text(text: Optional[str]) -> str:
    """Normalize text by trimming and collapsing whitespace"""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())


def extract_metrics_from_row(row: Any) -> Dict[str, Any]:
    """Extract numeric metrics from table row cells (excluding first two cells: card number and player name)"""
    metrics: Dict[str, Any] = {}
    cells = row.css("td.MuiTableCell-root")

    if len(cells) < 3:  # Need at least card number, player name, and one metric cell
        return metrics

    # Skip first two cells (card number and player name), extract from remaining cells
    metric_cells = cells[2:]

    # Try to extract column headers from table head for better metric names
    table = row.parent
    if table:
        header_rows = table.css("thead tr")
        grade_names = []

        for header_row in header_rows:
            header_cells = header_row.css("th")
            if len(header_cells) > 1:  # Skip first header (title column)
                for i, header_cell in enumerate(header_cells[1:]):
                    header_text = normalize_text(header_cell.text())
                    if header_text and header_text not in [
                        "Card",
                        "Player",
                        "Grade",
                    ]:  # Skip generic headers
                        grade_names.append(header_text)

    # Extract metrics from cells
    for i, cell in enumerate(metric_cells):
        text = normalize_text(cell.text())

        # Try to parse as integer
        if text and text.replace(",", "").replace("-", "").isdigit():
            value = int(text.replace(",", "").replace("-", "0"))

            # Use grade names if available, otherwise use generic names
            if i < len(grade_names) and grade_names[i]:
                key = f"grade_{grade_names[i]}"
            else:
                # Common grade patterns
                if i == len(metric_cells) - 1:  # Last cell is usually total
                    key = "total"
                else:
                    key = f"grade_{i}"

            metrics[key] = value
        elif text and text != "-":
            # Store non-numeric values as strings
            if i < len(grade_names) and grade_names[i]:
                key = f"grade_{grade_names[i]}"
            else:
                key = f"grade_{i}"
            metrics[key] = text

    return metrics


def extract_card_urls_from_cell(title_cell: Any) -> List[str]:
    """Extract all URLs from the title cell"""
    card_urls: List[str] = []
    anchors = title_cell.css("a[href]")

    for anchor in anchors:
        href = anchor.attributes.get("href", "") if anchor.attributes else ""
        # Filter out non-destinations: href that are empty, #, javascript:*
        if href and not href.startswith("#") and not href.startswith("javascript:"):
            # Convert to absolute URL
            absolute_url = urljoin(BASE_URL, href)
            card_urls.append(absolute_url)

    # De-duplicate while preserving order
    seen_urls = set()
    unique_urls = []
    for url in card_urls:
        if url not in seen_urls:
            seen_urls.add(url)
            unique_urls.append(url)

    return unique_urls


def extract_cards_from_set_page(
    html: str, sport: str, year: str, set_title: str, set_url: str
) -> Dict[str, Any]:
    """
    Extract cards from set page HTML.

    Args:
        html: Raw HTML content
        sport: Sport name (e.g., "Baseball")
        year: Year string (e.g., "1989")
        set_title: Set title (e.g., "Donruss")
        set_url: Set page URL

    Returns:
        dict with 'cards' and 'totals' keys:
        {
            'cards': [
                {
                    'sport': 'Baseball',
                    'year': '1989',
                    'set_title': 'Donruss',
                    'set_url': '...',
                    'card_name': 'Gary Carter',
                    'card_urls': ['https://...'],
                    'metrics': {'grade_10': 1, 'total': 15, ...}
                }
            ],
            'totals': [
                {
                    'scope': 'set',
                    'sport': 'Baseball',
                    'year': '1989',
                    'set_title': 'Donruss',
                    'card_name': None,
                    'metrics': {'total': 592, ...}
                }
            ]
        }
    """
    tree = HTMLParser(html)
    cards = []
    totals = []

    # Find table body rows
    rows = tree.css("tbody tr.MuiTableRow-root")

    for row in rows:
        # Get all cells in the row
        cells = row.css("td.MuiTableCell-root")
        if len(cells) < 2:  # Need at least card number and player name
            continue

        # First cell contains card number, second cell contains player name
        card_number_cell = cells[0]
        title_cell = cells[1]  # This is the cell with player name and links

        # Extract card number and player name
        card_number = normalize_text(card_number_cell.text())
        card_name = normalize_text(title_cell.text())

        if not card_name or not card_number:
            continue

        # Check if this is a TOTALS row
        if card_name.upper() == "TOTALS":
            # Extract metrics from this TOTALS row
            metrics = extract_metrics_from_row(row)

            totals.append(
                {
                    "scope": "set",
                    "sport": sport,
                    "year": year,
                    "set_title": set_title,
                    "card_name": None,
                    "metrics": metrics,
                }
            )
            continue

        # Extract URLs from title cell (player name cell)
        card_urls = extract_card_urls_from_cell(title_cell)

        # Extract metrics from remaining cells (starting from index 2)
        metrics = extract_metrics_from_row(row)

        cards.append(
            {
                "sport": sport,
                "year": year,
                "set_title": set_title,
                "set_url": set_url,
                "card_name": card_name,
                "card_urls": card_urls,
                "metrics": metrics,
            }
        )

    return {"cards": cards, "totals": totals}


def extract_cards_from_url(
    set_url: str, set_title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract cards from a set URL.

    Args:
        set_url: Set page URL
        set_title: Clean set title (optional, will extract from URL if not provided)

    Returns:
        dict with 'cards' and 'totals' keys
    """
    # Extract sport, year, and set from URL
    url_parts = set_url.rstrip("/").split("/")
    if len(url_parts) < 5:
        raise ValueError(f"Invalid set URL format: {set_url}")

    # Use provided set_title if available, otherwise extract from URL
    if set_title is None:
        # Extract from URL and clean it
        raw_set_title = url_parts[-1]  # "Donruss" or "Donruss?setName=Light+Blue"
        # Remove query parameters to get clean set title
        set_title = (
            raw_set_title.split("?")[0] if "?" in raw_set_title else raw_set_title
        )

    year = url_parts[-2]  # "1989"
    sport = url_parts[-3]  # "Baseball"

    print(f"    Fetching cards for {sport} {year} {set_title}")
    html = fetch_rendered_html(set_url)

    return extract_cards_from_set_page(html, sport, year, set_title, set_url)


def main() -> None:
    """Test the cards scraper"""
    # Test URLs
    test_urls = [
        "https://my.taggrading.com/pop-report/Baseball/1989/Donruss",
        "https://my.taggrading.com/pop-report/Hockey/1989/Topps",
    ]

    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing Cards Scraper: {url}")
        print("=" * 60)

        try:
            result = extract_cards_from_url(url)

            print(f"Found {len(result['cards'])} cards:")
            for i, card_data in enumerate(result["cards"][:5]):  # Show first 5
                print(f"  {i+1}. {card_data['card_name']}")
                print(f"     URLs: {len(card_data['card_urls'])} found")
                print(f"     Metrics: {len(card_data['metrics'])} grades")
                print()

            if len(result["cards"]) > 5:
                print(f"  ... and {len(result['cards']) - 5} more cards")

            print(f"Found {len(result['totals'])} totals:")
            for total in result["totals"]:
                print(f"  TOTAL ({total['scope']}): {total['metrics']}")

        except Exception as e:
            print(f"Error scraping {url}: {e}")


if __name__ == "__main__":
    main()
