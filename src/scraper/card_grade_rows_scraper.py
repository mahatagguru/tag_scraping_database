#!/usr/bin/env python3
"""
Card Grade Rows Scraper

Scrapes individual grade rows from card pages like:
- https://my.taggrading.com/pop-report/Baseball/1989/Donruss/Gary Carter/53

Extracts detailed grade information including rank, TAG grade, report URLs, dates, and certification numbers.
This implements the fifth level of the scraping pipeline: Sport → Year → Set → Card → Grade Rows.
"""

from datetime import datetime
import re
import sys
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

BASE_URL = "https://my.taggrading.com"


def fetch_rendered_html(url):
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


def normalize_text(text):
    """Normalize text by trimming and collapsing whitespace"""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())


def parse_date_to_iso(date_text):
    """
    Attempt to parse date text to ISO format.
    Returns (raw_text, datetime_object) tuple.
    """
    if not date_text:
        return date_text, None

    raw_text = normalize_text(date_text)

    # Common date formats
    date_patterns = [
        # MM-DD-YYYY
        (
            r"(\d{1,2})-(\d{1,2})-(\d{4})",
            lambda m: f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}",
        ),
        # MM/DD/YYYY
        (
            r"(\d{1,2})/(\d{1,2})/(\d{4})",
            lambda m: f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}",
        ),
        # YYYY-MM-DD (already ISO)
        (
            r"(\d{4})-(\d{1,2})-(\d{1,2})",
            lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}",
        ),
    ]

    for pattern, formatter in date_patterns:
        match = re.match(pattern, raw_text)
        if match:
            try:
                iso_date_str = formatter(match)
                # Validate the date and convert to datetime object
                dt = datetime.fromisoformat(iso_date_str)
                return raw_text, dt
            except ValueError:
                continue

    return raw_text, None


def extract_report_url_from_cell(cell):
    """Extract report URL from a table cell"""
    anchor = cell.css_first("a[href]")
    if not anchor:
        return None

    href = anchor.attributes.get("href", "")
    if href and not href.startswith("#") and not href.startswith("javascript:"):
        # Normalize URL to absolute format
        normalized_url = urljoin(BASE_URL, href)
        # Ensure we have a valid URL
        if normalized_url.startswith("http"):
            return normalized_url

    return None


def map_columns_by_headers(header_row):
    """
    Map table columns by header text.
    Returns a dictionary mapping column names to indices.
    """
    column_map = {}
    headers = header_row.css("th")

    for i, header in enumerate(headers):
        header_text = normalize_text(header.text()).lower()

        # Handle Material-UI icons that might be appended to headers
        if (
            "rank" in header_text
            and "grade" not in header_text
            and "by" not in header_text
        ):
            column_map["rank"] = i
        elif "tag grade" in header_text:
            column_map["tag_grade"] = i
        elif "view report" in header_text or "report" in header_text:
            column_map["report_url"] = i
        elif "rank by grade" in header_text:
            column_map["rank_by_grade"] = i
        elif "chronology" in header_text and "grade" not in header_text:
            column_map["chronology"] = i
        elif "chron by grade" in header_text:
            column_map["chron_by_grade"] = i
        elif "completed" in header_text:
            column_map["completed_date"] = i
        elif "cert number" in header_text:
            column_map["cert_number"] = i

    return column_map


def extract_grade_rows_from_card_page(
    html, sport, year, set_title, card_name, card_url
):
    """
    Extract grade rows from card page HTML.

    Args:
        html: Raw HTML content
        sport: Sport name (e.g., "Baseball")
        year: Year string (e.g., "1989")
        set_title: Set title (e.g., "Donruss")
        card_name: Card name (e.g., "Gary Carter")
        card_url: Card page URL

    Returns:
        list of grade row dictionaries with all required fields
    """
    tree = HTMLParser(html)
    grade_rows = []

    # Find the main results table
    tables = tree.css("table.MuiTable-root")
    if not tables:
        print("      No tables found on card page")
        return grade_rows

    # Look for table with grade-related headers
    target_table = None
    column_map = {}

    for table in tables:
        header_rows = table.css("thead tr")
        for header_row in header_rows:
            # Try to map columns by headers
            temp_map = map_columns_by_headers(header_row)
            if len(temp_map) >= 4:  # Need at least rank, grade, report_url, cert_number
                target_table = table
                column_map = temp_map
                break
        if target_table:
            break

    if not target_table:
        print("      No suitable grade table found")
        return grade_rows

    print(f"      Found grade table with {len(column_map)} mapped columns")

    # Extract data rows
    data_rows = target_table.css("tbody tr.MuiTableRow-root")

    for row in data_rows:
        cells = row.css("td.MuiTableCell-root")
        if len(cells) < max(column_map.values()) + 1:
            continue

        # Extract data based on column mapping
        row_data = {
            "sport": sport,
            "year": year,
            "set_title": set_title,
            "card_name": card_name,
            "card_url": card_url,
        }

        # Extract each field based on column mapping
        for field, col_index in column_map.items():
            if col_index < len(cells):
                cell = cells[col_index]

                if field == "report_url":
                    # Special handling for report URL
                    report_url = extract_report_url_from_cell(cell)
                    row_data[field] = report_url
                elif field == "completed_date":
                    # Special handling for date - prefer value attribute if available
                    value_attr = cell.attributes.get("value", "")
                    if value_attr and "T" in value_attr:  # ISO timestamp format
                        # Parse ISO timestamp to get date
                        try:
                            from datetime import datetime

                            iso_timestamp = value_attr
                            if iso_timestamp.endswith("Z"):
                                iso_timestamp = iso_timestamp[:-1]  # Remove Z suffix
                            dt = datetime.fromisoformat(iso_timestamp)
                            row_data["completed_date_raw"] = dt.strftime("%m-%d-%Y")
                            row_data["completed_date_iso"] = (
                                dt  # Store as datetime object, not string
                            )
                        except Exception:
                            # Fallback to display text
                            date_text = normalize_text(cell.text())
                            raw_date, dt = parse_date_to_iso(date_text)
                            row_data["completed_date_raw"] = raw_date
                            row_data["completed_date_iso"] = (
                                dt  # Store as datetime object, not string
                            )
                    else:
                        # Use display text
                        date_text = normalize_text(cell.text())
                        raw_date, dt = parse_date_to_iso(date_text)
                        row_data["completed_date_raw"] = raw_date
                        row_data["completed_date_iso"] = (
                            dt  # Store as datetime object, not string
                        )
                else:
                    # Regular text field - handle special cases
                    if field in ["chronology", "chron_by_grade"]:
                        # For chronology fields, always use display text to get "1ST" instead of "1"
                        row_data[field] = normalize_text(cell.text())
                    else:
                        # For other fields, prefer value attribute if available
                        value_attr = cell.attributes.get("value", "")
                        if (
                            value_attr and value_attr != "0"
                        ):  # Use value attribute if it's not the default '0'
                            row_data[field] = value_attr
                        else:
                            # Fallback to display text
                            row_data[field] = normalize_text(cell.text())

        # Ensure we have a cert_number (required field)
        if "cert_number" not in row_data or not row_data["cert_number"]:
            print("        Skipping row without cert_number")
            continue

        # Skip rows with missing essential data
        if not row_data.get("tag_grade"):
            print("        Skipping row without tag_grade")
            continue

        # Validate report URL if present
        if "report_url" in row_data and row_data["report_url"]:
            if not row_data["report_url"].startswith("http"):
                print(
                    f"        Warning: Invalid report URL format: {row_data['report_url']}"
                )
                row_data["report_url"] = None

        grade_rows.append(row_data)

    return grade_rows


def extract_grade_rows_from_url(card_url, set_title=None):
    """
    Extract grade rows from a card URL.

    Args:
        card_url: Card page URL
        set_title: Clean set title (optional, will extract from URL if not provided)

    Returns:
        list of grade row dictionaries
    """
    # Extract sport, year, set, and card from URL
    url_parts = card_url.rstrip("/").split("/")
    if len(url_parts) < 6:
        raise ValueError(f"Invalid card URL format: {card_url}")

    card_name = url_parts[-2]  # "Gary Carter"

    # Use provided set_title if available, otherwise extract from URL and clean it
    if set_title is None:
        raw_set_title = url_parts[-3]  # "Donruss" or potentially "Donruss?setName=..."
        # Remove query parameters to get clean set title
        set_title = (
            raw_set_title.split("?")[0] if "?" in raw_set_title else raw_set_title
        )

    year = url_parts[-4]  # "1989"
    sport = url_parts[-5]  # "Baseball"

    print(f"      Fetching grade rows for {sport} {year} {set_title} {card_name}")
    html = fetch_rendered_html(card_url)

    return extract_grade_rows_from_card_page(
        html, sport, year, set_title, card_name, card_url
    )


def main():
    """Test the card grade rows scraper"""
    # Test URLs
    test_urls = [
        "https://my.taggrading.com/pop-report/Baseball/1989/Donruss/Gary Carter/53",
        "https://my.taggrading.com/pop-report/Hockey/1989/Topps/Mario Lemieux/1",
    ]

    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing Card Grade Rows Scraper: {url}")
        print("=" * 60)

        try:
            grade_rows = extract_grade_rows_from_url(url)

            print(f"Found {len(grade_rows)} grade rows:")
            for i, row in enumerate(grade_rows[:3]):  # Show first 3
                print(f"  {i+1}. Grade: {row.get('tag_grade', 'N/A')}")
                print(f"     Rank: {row.get('rank', 'N/A')}")
                print(f"     Cert: {row.get('cert_number', 'N/A')}")
                print(f"     Report URL: {row.get('report_url', 'N/A')}")
                print(f"     Completed: {row.get('completed_date_raw', 'N/A')}")
                print()

            if len(grade_rows) > 3:
                print(f"  ... and {len(grade_rows) - 3} more grade rows")

            # Show field mapping info
            if grade_rows:
                sample_row = grade_rows[0]
                print(f"Sample row fields: {list(sample_row.keys())}")

        except Exception as e:
            print(f"Error scraping {url}: {e}")


if __name__ == "__main__":
    main()
