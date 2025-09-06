import sys
from typing import Any, Dict, List
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

CATEGORY_YEAR_URL = "https://my.taggrading.com/pop-report/Hockey"

def fetch_rendered_html(url: str) -> str:
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
        html = page.content()
        browser.close()
        return html

def extract_years(html: str) -> List[Dict[str, Any]]:
    tree = HTMLParser(html)
    years: List[Dict[str, Any]] = []
    base_url = "https://my.taggrading.com"
    
    # Find the table body rows (skip header/footer)
    for row in tree.css('tbody tr.MuiTableRow-root'):
        cells = row.css('td.MuiTableCell-root')
        if len(cells) < 4:
            continue
            
        # Get the first cell (title cell)
        title_cell = cells[0]
        
        # Extract year from the cell text
        year = title_cell.text(strip=True)
        
        # Extract all anchor URLs from the title cell
        year_urls: List[str] = []
        anchors = title_cell.css('a[href]')
        for anchor in anchors:
            href = anchor.attributes.get('href', '') if anchor.attributes else ''
            # Filter out non-destinations: href that are empty, #, javascript:*
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                # Convert to absolute URL
                absolute_url = urljoin(base_url, href)
                year_urls.append(absolute_url)
        
        # De-duplicate while preserving order
        seen_urls = set()
        unique_urls: List[str] = []
        for url in year_urls:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_urls.append(url)
        
        num_sets = cells[1].text(strip=True)
        total_items = cells[2].text(strip=True)
        total_graded = cells[3].text(strip=True)
        
        years.append({
            'year': year,
            'year_urls': unique_urls,
            'num_sets': num_sets,
            'total_items': total_items,
            'total_graded': total_graded
        })
    return years

def extract_year_urls(html: str) -> List[str]:
    tree = HTMLParser(html)
    urls: List[str] = []
    for a in tree.css('a'):
        href = a.attributes.get('href', '') if a.attributes else ''
        if href and href.startswith('/pop-report/') and href.count('/') == 3:
            urls.append('https://my.taggrading.com' + href)
    return urls

def fetch_and_print_years(url: str) -> None:
    html = fetch_rendered_html(url)
    with open("debug_playwright_year_rendered.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved rendered HTML to debug_playwright_year_rendered.html")
    years = extract_years(html)
    print(f"Found {len(years)} years:")
    for y in years:
        print(f"- {y['year']} | URLs: {y['year_urls']} | sets: {y['num_sets']} | items: {y['total_items']} | graded: {y['total_graded']}")

if __name__ == "__main__":
    fetch_and_print_years(CATEGORY_YEAR_URL)
