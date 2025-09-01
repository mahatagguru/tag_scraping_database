import sys
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

SET_URL = "https://my.taggrading.com/pop-report/Baseball/1989"

def fetch_rendered_html(url):
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

def extract_sets(html):
    tree = HTMLParser(html)
    sets = []
    base_url = "https://my.taggrading.com"
    
    # Find the table body rows for sets
    for row in tree.css('tbody tr.MuiTableRow-root'):
        # Get the first cell (title cell)
        title_cell = row.css_first('td')
        if not title_cell:
            continue
            
        # Extract set title from the cell text (preserve visible text like <b>Classic</b> Light Blue)
        # Get all text content while preserving structure
        set_title = title_cell.text(strip=True)
        # Normalize whitespace (collapse multiple spaces)
        set_title = ' '.join(set_title.split())
        
        # Extract all anchor URLs from the title cell
        set_urls = []
        anchors = title_cell.css('a[href]')
        for anchor in anchors:
            href = anchor.attributes.get('href', '')
            # Filter out non-destinations: href that are empty, #, javascript:*
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                # Convert to absolute URL
                absolute_url = urljoin(base_url, href)
                set_urls.append(absolute_url)
        
        # De-duplicate while preserving order
        seen_urls = set()
        unique_urls = []
        for url in set_urls:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_urls.append(url)
        
        # Grade totals: all cells with MuiTableCell-root MuiTableCell-body MuiTableCell-alignCenter
        grade_cells = row.css('td.MuiTableCell-root.MuiTableCell-body.MuiTableCell-alignCenter')
        grades = [cell.text(strip=True) for cell in grade_cells]
        
        sets.append({
            'set_title': set_title,
            'set_urls': unique_urls,
            'set_name': set_title,  # Keep for backward compatibility
            'grades': grades
        })
    return sets

def extract_set_urls(html):
    tree = HTMLParser(html)
    urls = []
    for a in tree.css('a'):
        href = a.attributes.get('href', '')
        if href.startswith('/pop-report/') and href.count('/') == 4:
            urls.append('https://my.taggrading.com' + href)
    return urls

def fetch_and_print_sets(url):
    html = fetch_rendered_html(url)
    with open("debug_playwright_set_rendered.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved rendered HTML to debug_playwright_set_rendered.html")
    sets = extract_sets(html)
    print(f"Found {len(sets)} sets:")
    for s in sets:
        print(f"- {s['set_title']} | URLs: {s['set_urls']} | grades: {s['grades']}")

if __name__ == "__main__":
    fetch_and_print_sets(SET_URL)
