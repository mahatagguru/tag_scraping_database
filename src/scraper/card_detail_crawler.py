import sys
from typing import Any, Dict, List, Optional

from selectolax.parser import HTMLParser

CARD_DETAIL_URL = (
    "https://my.taggrading.com/pop-report/Hockey/1989/O-Pee-Chee/Mario%20Lemieux/1"
)


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


def extract_card_details(html: str) -> Dict[str, Any]:
    tree = HTMLParser(html)
    # Extract card image URL
    card_img_el = tree.css_first('img[src*="card-images"]')
    card_image_url = card_img_el.attributes.get("src") if card_img_el else None

    # Extract player name
    player_name_el = tree.css_first("div.jss139 span.MuiTypography-body1:last-child")
    player_name = player_name_el.text(strip=True) if player_name_el else None

    # Extract set name
    set_name_el = tree.css_first("div.jss140 span.MuiTypography-body1:last-child")
    set_name = set_name_el.text(strip=True) if set_name_el else None

    # Extract subset name
    subset_name_el = tree.css_first("div.jss141 span.MuiTypography-body1:last-child")
    subset_name = subset_name_el.text(strip=True) if subset_name_el else None

    # Extract variation
    variation_el = tree.css_first("div.jss142 span.MuiTypography-body1:last-child")
    variation = variation_el.text(strip=True) if variation_el else None

    # Extract table data as before
    details_list: List[Dict[str, Any]] = []
    table = tree.css_first("table.MuiTable-root")
    if table:
        for row in table.css("tbody tr"):
            cells = row.css("td")
            if len(cells) < 8:
                continue  # skip incomplete rows
            # Get the link element safely
            link_el = cells[2].css_first("a")
            view_report_url = None
            if link_el and link_el.attributes:
                view_report_url = link_el.attributes.get("href")

            details = {
                "rank": cells[0].text(strip=True),
                "tag_grade": cells[1].text(strip=True),
                "view_report": view_report_url,
                "rank_by_grade": cells[3].text(strip=True),
                "chronology": cells[4].text(strip=True),
                "chron_by_grade": cells[5].text(strip=True),
                "completed": cells[6].text(strip=True),
                "cert_number": cells[7].text(strip=True),
            }
            details_list.append(details)

    # Return all extracted info
    return {
        "card_image_url": card_image_url,
        "player_name": player_name,
        "set_name": set_name,
        "subset_name": subset_name,
        "variation": variation,
        "table_rows": details_list,
    }


def extract_cert_urls(html: str) -> List[str]:
    tree = HTMLParser(html)
    urls: List[str] = []
    for a in tree.css("table.MuiTable-root a"):
        href = a.attributes.get("href", "") if a.attributes else ""
        if href and "/card/" in href:
            if href.startswith("http"):
                urls.append(href)
            else:
                urls.append("https://my.taggrading.com" + href)
    return urls


def fetch_and_print_card_details(url: str) -> None:
    html = fetch_rendered_html(url)
    with open("debug_playwright_card_detail_rendered.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved rendered HTML to debug_playwright_card_detail_rendered.html")
    details = extract_card_details(html)
    print("Extracted card details:")
    print(f"Card Image URL: {details['card_image_url']}")
    print(f"Player Name: {details['player_name']}")
    print(f"Set Name: {details['set_name']}")
    print(f"Subset Name: {details['subset_name']}")
    print(f"Variation: {details['variation']}")
    print("Table Rows:")
    for idx, row in enumerate(details["table_rows"], 1):
        print(f"Row {idx}:")
        for k, v in row.items():
            print(f"  - {k}: {v}")


if __name__ == "__main__":
    fetch_and_print_card_details(CARD_DETAIL_URL)
