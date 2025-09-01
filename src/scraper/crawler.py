"""
Main crawling logic for TAG Pop Report scraper.
Traverses category, year, set, and card pages, extracts embedded JSON or HTML, and upserts data into the database.
"""
import json
import re

import requests
from selectolax.parser import HTMLParser

CATEGORY_URL = "https://my.taggrading.com/pop-report"

# --- Playwright integration ---
def fetch_rendered_html(url):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is not installed. Please run: pip install playwright && python3 -m playwright install")
        raise
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        html = page.content()
        browser.close()
        return html

def extract_categories(html):
    tree = HTMLParser(html)
    categories = []
    # Each category is in a MuiGrid-item MuiGrid-grid-lg-2
    for card in tree.css('.MuiGrid-item.MuiGrid-grid-lg-2'):
        name_el = card.css_first('h6')
        img_el = card.css_first('img')
        if not (name_el and img_el):
            continue
        name = name_el.text(strip=True)
        img = img_el.attributes.get('src')
        categories.append({'name': name, 'img': img})
    return categories

def extract_category_urls(html):
    tree = HTMLParser(html)
    urls = []
    for a in tree.css('a'):
        href = a.attributes.get('href', '')
        if href.startswith('/pop-report/') and href.count('/') == 2:
            urls.append('https://my.taggrading.com' + href)
    return urls

def fetch_and_print_categories(url):
    html = fetch_rendered_html(url)
    # Save the rendered HTML for inspection
    with open("debug_playwright_rendered.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved rendered HTML to debug_playwright_rendered.html")
    categories = extract_categories(html)
    print(f"Found {len(categories)} categories:")
    for cat in categories:
        print(f"- {cat['name']} | img: {cat['img']}")

if __name__ == "__main__":
    fetch_and_print_categories(CATEGORY_URL)
