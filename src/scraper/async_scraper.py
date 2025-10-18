#!/usr/bin/env python3
"""
Async web scraper with intelligent browser detection and lightweight HTML fetching.
"""

import asyncio
import re
import sys
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

from .async_client import AsyncScrapingSession


class AsyncWebScraper:
    """Async web scraper with intelligent browser vs HTTP detection."""
    
    def __init__(
        self,
        max_concurrent: int = 10,
        rate_limit: float = 1.0,
        enable_cache: bool = True,
        use_playwright_fallback: bool = True,
    ):
        """
        Initialize async web scraper.
        
        Args:
            max_concurrent: Maximum concurrent requests
            rate_limit: Rate limit between requests
            enable_cache: Enable response caching
            use_playwright_fallback: Fall back to Playwright for JS-heavy pages
        """
        self.max_concurrent = max_concurrent
        self.rate_limit = rate_limit
        self.enable_cache = enable_cache
        self.use_playwright_fallback = use_playwright_fallback
        
        # Track which URLs need JavaScript
        self._js_required_urls = set()
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = AsyncScrapingSession(
            max_concurrent=self.max_concurrent,
            rate_limit=self.rate_limit,
            enable_cache=self.enable_cache,
        )
        await self.session.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.session.__aexit__(exc_type, exc_val, exc_tb)
        
    async def fetch_html_async(self, url: str, force_playwright: bool = False) -> str:
        """
        Fetch HTML content, using aiohttp first and Playwright as fallback.
        
        Args:
            url: URL to fetch
            force_playwright: Force use of Playwright even if not needed
            
        Returns:
            HTML content
        """
        # If we know this URL needs JS or it's forced, use Playwright
        if force_playwright or url in self._js_required_urls:
            return await self._fetch_with_playwright(url)
            
        try:
            # Try lightweight HTTP fetch first
            html = await self.session.client.fetch_html(url)
            
            # Check if the page seems to need JavaScript
            if self._needs_javascript(html):
                self._js_required_urls.add(url)
                print(f"🔄 URL {url} requires JavaScript, switching to Playwright")
                return await self._fetch_with_playwright(url)
                
            return html
            
        except Exception as e:
            if self.use_playwright_fallback:
                print(f"⚠️  HTTP fetch failed for {url}: {e}, trying Playwright")
                return await self._fetch_with_playwright(url)
            else:
                raise
                
    def _needs_javascript(self, html: str) -> bool:
        """
        Heuristically determine if a page needs JavaScript to render content.
        
        Args:
            html: HTML content to analyze
            
        Returns:
            True if JavaScript is likely required
        """
        # Check for common indicators that JavaScript is needed
        js_indicators = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'ng-',  # Angular directives
            r'v-',   # Vue directives
            r'data-react',  # React data attributes
            r'__NEXT_DATA__',  # Next.js
            r'window\.__INITIAL_STATE__',  # Common JS state patterns
            r'<noscript>',  # NoScript tags often indicate JS dependency
            r'class="loading"',  # Loading indicators
            r'id="app"',  # SPA containers
        ]
        
        # If the HTML is very small, it might be a shell
        if len(html) < 1000:
            return True
            
        # Check for specific patterns
        for pattern in js_indicators:
            if re.search(pattern, html, re.IGNORECASE | re.DOTALL):
                return True
                
        # Check if there's minimal content (likely a SPA shell)
        content_indicators = [
            r'<table[^>]*>.*?</table>',  # Tables with content
            r'<div[^>]*class="[^"]*card[^"]*"[^>]*>',  # Card containers
            r'<ul[^>]*>.*?</ul>',  # Lists
        ]
        
        has_content = any(re.search(pattern, html, re.IGNORECASE | re.DOTALL) 
                         for pattern in content_indicators)
        
        # If no substantial content found, likely needs JS
        return not has_content
        
    async def _fetch_with_playwright(self, url: str) -> str:
        """
        Fetch HTML using Playwright for JavaScript-heavy pages.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError(
                "Playwright is not installed. Please run: pip install playwright && python3 -m playwright install"
            )
            
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url, timeout=60000)
                await page.wait_for_load_state("networkidle")
                html = await page.content()
                return html
            finally:
                await browser.close()
                
    async def extract_categories_async(self, url: str) -> List[Dict[str, Any]]:
        """Extract categories from the main page."""
        html = await self.fetch_html_async(url)
        return self._extract_categories_from_html(html)
        
    async def extract_years_async(self, url: str) -> List[Dict[str, Any]]:
        """Extract years from a category page."""
        html = await self.fetch_html_async(url)
        return self._extract_years_from_html(html)
        
    async def extract_sets_async(self, url: str) -> List[Dict[str, Any]]:
        """Extract sets from a year page."""
        html = await self.fetch_html_async(url)
        return self._extract_sets_from_html(html)
        
    async def extract_cards_async(self, url: str) -> List[Dict[str, Any]]:
        """Extract cards from a set page."""
        html = await self.fetch_html_async(url)
        return self._extract_cards_from_html(html)
        
    async def extract_card_details_async(self, url: str) -> Dict[str, Any]:
        """Extract card details from a card page."""
        html = await self.fetch_html_async(url)
        return self._extract_card_details_from_html(html)
        
    async def fetch_multiple_async(self, urls: List[str]) -> List[Tuple[str, Optional[str]]]:
        """Fetch multiple URLs concurrently."""
        return await self.session.client.fetch_multiple(urls, self.max_concurrent)
        
    def _extract_categories_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Extract categories from HTML content."""
        tree = HTMLParser(html)
        categories = []
        
        # Look for category links or table rows
        category_elements = tree.css('a[href*="/pop-report/"]') or tree.css('tr')
        
        for element in category_elements:
            try:
                # Extract category name
                name = element.text(strip=True)
                if not name or name.upper() == 'TOTALS':
                    continue
                    
                # Extract image URL if available
                img_element = element.css_first('img')
                img_url = img_element.attributes.get('src') if img_element else None
                
                # Extract metrics from table cells if available
                cells = element.css('td')
                num_sets = None
                total_items = None
                total_graded = None
                
                if len(cells) >= 3:
                    try:
                        num_sets = int(cells[1].text(strip=True)) if cells[1].text(strip=True).isdigit() else None
                        total_items = int(cells[2].text(strip=True)) if cells[2].text(strip=True).isdigit() else None
                        total_graded = int(cells[3].text(strip=True)) if len(cells) > 3 and cells[3].text(strip=True).isdigit() else None
                    except (ValueError, IndexError):
                        pass
                
                categories.append({
                    'name': name,
                    'image_url': img_url,
                    'num_sets': num_sets,
                    'total_items': total_items,
                    'total_graded': total_graded,
                })
                
            except Exception as e:
                print(f"Error extracting category: {e}")
                continue
                
        return categories
        
    def _extract_years_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Extract years from HTML content."""
        tree = HTMLParser(html)
        years = []
        
        # Look for year links or table rows
        year_elements = tree.css('a[href*="/pop-report/"]') or tree.css('tr')
        
        for element in year_elements:
            try:
                # Extract year
                year_text = element.text(strip=True)
                if not year_text or year_text.upper() == 'TOTALS' or not year_text.isdigit():
                    continue
                    
                year = int(year_text)
                
                # Extract metrics from table cells if available
                cells = element.css('td')
                num_sets = None
                total_items = None
                total_graded = None
                
                if len(cells) >= 3:
                    try:
                        num_sets = int(cells[1].text(strip=True)) if cells[1].text(strip=True).isdigit() else None
                        total_items = int(cells[2].text(strip=True)) if cells[2].text(strip=True).isdigit() else None
                        total_graded = int(cells[3].text(strip=True)) if len(cells) > 3 and cells[3].text(strip=True).isdigit() else None
                    except (ValueError, IndexError):
                        pass
                
                years.append({
                    'year': str(year),
                    'num_sets': num_sets,
                    'total_items': total_items,
                    'total_graded': total_graded,
                })
                
            except Exception as e:
                print(f"Error extracting year: {e}")
                continue
                
        return years
        
    def _extract_sets_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Extract sets from HTML content."""
        tree = HTMLParser(html)
        sets = []
        
        # Look for set links or table rows
        set_elements = tree.css('a[href*="/pop-report/"]') or tree.css('tr')
        
        for element in set_elements:
            try:
                # Extract set name
                set_name = element.text(strip=True)
                if not set_name or set_name.upper() == 'TOTALS':
                    continue
                    
                # Extract grades/metrics
                cells = element.css('td')
                grades = []
                
                if len(cells) > 1:
                    for cell in cells[1:]:
                        cell_text = cell.text(strip=True)
                        if cell_text:
                            grades.append(cell_text)
                
                sets.append({
                    'set_name': set_name,
                    'grades': grades,
                })
                
            except Exception as e:
                print(f"Error extracting set: {e}")
                continue
                
        return sets
        
    def _extract_cards_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Extract cards from HTML content."""
        tree = HTMLParser(html)
        cards = []
        
        # Look for card links or table rows
        card_elements = tree.css('a[href*="/pop-report/"]') or tree.css('tr')
        
        for element in card_elements:
            try:
                # Extract card name
                card_name = element.text(strip=True)
                if not card_name or card_name.upper() == 'TOTALS':
                    continue
                    
                # Extract card URL
                link_element = element.css_first('a')
                card_url = link_element.attributes.get('href') if link_element else None
                
                if card_url:
                    card_url = urljoin("https://my.taggrading.com", card_url)
                
                cards.append({
                    'card_name': card_name,
                    'card_url': card_url,
                })
                
            except Exception as e:
                print(f"Error extracting card: {e}")
                continue
                
        return cards
        
    def _extract_card_details_from_html(self, html: str) -> Dict[str, Any]:
        """Extract card details from HTML content."""
        tree = HTMLParser(html)
        
        # Extract player name
        player_name = None
        player_element = tree.css_first('h1, .player-name, .card-title')
        if player_element:
            player_name = player_element.text(strip=True)
            
        # Extract card image
        card_image_url = None
        img_element = tree.css_first('img[src*="card"], img[alt*="card"]')
        if img_element:
            card_image_url = img_element.attributes.get('src')
            
        # Extract subset name
        subset_name = None
        subset_element = tree.css_first('.subset, .variation')
        if subset_element:
            subset_name = subset_element.text(strip=True)
            
        # Extract grade rows from table
        table_rows = []
        table = tree.css_first('table')
        if table:
            rows = table.css('tr')
            for row in rows:
                cells = row.css('td')
                if len(cells) >= 3:
                    try:
                        row_data = {
                            'rank': cells[0].text(strip=True),
                            'tag_grade': cells[1].text(strip=True),
                            'completed': cells[2].text(strip=True),
                            'cert_number': cells[3].text(strip=True) if len(cells) > 3 else None,
                        }
                        table_rows.append(row_data)
                    except Exception:
                        continue
                        
        return {
            'player_name': player_name,
            'card_image_url': card_image_url,
            'subset_name': subset_name,
            'table_rows': table_rows,
        }
        
    def get_js_required_urls(self) -> List[str]:
        """Get list of URLs that require JavaScript."""
        return list(self._js_required_urls)
        
    def clear_js_cache(self) -> None:
        """Clear the JavaScript requirement cache."""
        self._js_required_urls.clear()
