import sys
from typing import Any, Dict, List
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

CARD_SET_URL = "https://my.taggrading.com/pop-report/Hockey/1989/O-Pee-Chee"


def fetch_rendered_html(url: str) -> str:
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


def extract_cards(html: str) -> List[Dict[str, Any]]:
    tree = HTMLParser(html)
    cards: List[Dict[str, Any]] = []
    base_url = "https://my.taggrading.com"

    # Find the table body rows for cards
    for row in tree.css("tbody tr.MuiTableRow-root"):
        # Get the first cell (title cell)
        cells = row.css("td.MuiTableCell-root")
        if len(cells) < 2:
            continue

        title_cell = cells[0]

        # Extract card number from the cell text
        card_number = title_cell.text(strip=True)

        # Extract all anchor URLs from the title cell
        card_urls = []
        anchors = title_cell.css("a[href]")
        for anchor in anchors:
            href = anchor.attributes.get("href", "")
            # Filter out non-destinations: href that are empty, #, javascript:*
            if href and not href.startswith("#") and not href.startswith("javascript:"):
                # Convert to absolute URL
                absolute_url = urljoin(base_url, href)
                card_urls.append(absolute_url)

        # De-duplicate while preserving order
        seen_urls = set()
        unique_urls = []
        for url in card_urls:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_urls.append(url)

        player = cells[1].text(strip=True)
        # Grade totals: all remaining cells (after card number and player)
        grades = [cell.text(strip=True) for cell in cells[2:]]

        cards.append(
            {
                "card_number": card_number,
                "card_urls": unique_urls,
                "player": player,
                "grades": grades,
            }
        )
    return cards


def extract_card_urls(html: str) -> List[str]:
    tree = HTMLParser(html)
    urls: set[str] = set()  # Use set to avoid duplicates

    for a in tree.css("a"):
        href = a.attributes.get("href", "") if a.attributes else ""

        # Look for card URLs that contain player names and card numbers
        # Pattern: /pop-report/Category/Year/Set/Player Name/CardNumber?setName=...
        if (
            href
            and href.startswith("/pop-report/")
            and href.count("/") >= 5
            and "?" in href  # At least 5 slashes for category/year/set/player/card
            and "setName=" in href  # Has query parameters
        ):  # Contains setName parameter
            # Remove grade-specific parameters to get base card URL
            base_url = href.split("&grades=")[0] if "&grades=" in href else href
            urls.add("https://my.taggrading.com" + base_url)

    return list(urls)  # Convert set back to list


def fetch_and_print_cards(url: str) -> None:
    html = fetch_rendered_html(url)
    with open("debug_playwright_card_rendered.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved rendered HTML to debug_playwright_card_rendered.html")
    cards = extract_cards(html)
    print(f"Found {len(cards)} cards:")
    for c in cards:
        print(
            f"- #{c['card_number']} | {c['player']} | URLs: {c['card_urls']} | grades: {c['grades']}"
        )


if __name__ == "__main__":
    fetch_and_print_cards(CARD_SET_URL)
