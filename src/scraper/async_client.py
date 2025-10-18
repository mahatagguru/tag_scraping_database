#!/usr/bin/env python3
"""
Async HTTP client with connection pooling and rate limiting for web scraping.
"""

import asyncio
import hashlib
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
from selectolax.parser import HTMLParser


class AsyncHTTPClient:
    """Async HTTP client with connection pooling, rate limiting, and caching."""
    
    def __init__(
        self,
        max_connections: int = 100,
        max_connections_per_host: int = 10,
        timeout: int = 30,
        rate_limit: float = 1.0,
        enable_cache: bool = True,
        cache_ttl: int = 3600,  # 1 hour
    ):
        """
        Initialize async HTTP client.
        
        Args:
            max_connections: Maximum total connections in pool
            max_connections_per_host: Maximum connections per host
            timeout: Request timeout in seconds
            rate_limit: Minimum delay between requests in seconds
            enable_cache: Enable response caching
            cache_ttl: Cache time-to-live in seconds
        """
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        
        # Rate limiting
        self._last_request_time = {}
        
        # Simple in-memory cache
        self._cache: Dict[str, Tuple[str, float]] = {}
        
        # Session will be created when needed
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            limit_per_host=self.max_connections_per_host,
            ttl_dns_cache=300,  # DNS cache for 5 minutes
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL."""
        return hashlib.md5(url.encode()).hexdigest()
        
    def _is_cache_valid(self, cache_entry: Tuple[str, float]) -> bool:
        """Check if cache entry is still valid."""
        if not self.enable_cache:
            return False
        _, timestamp = cache_entry
        return time.time() - timestamp < self.cache_ttl
        
    async def _rate_limit_request(self, host: str) -> None:
        """Apply rate limiting for host."""
        if self.rate_limit <= 0:
            return
            
        now = time.time()
        last_time = self._last_request_time.get(host, 0)
        elapsed = now - last_time
        
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
            
        self._last_request_time[host] = time.time()
        
    async def fetch_html(self, url: str, use_cache: bool = True) -> str:
        """
        Fetch HTML content from URL with caching and rate limiting.
        
        Args:
            url: URL to fetch
            use_cache: Whether to use cached response if available
            
        Returns:
            HTML content as string
        """
        if not self._session:
            raise RuntimeError("HTTP client not initialized. Use async context manager.")
            
        # Check cache first
        if use_cache and self.enable_cache:
            cache_key = self._get_cache_key(url)
            if cache_key in self._cache:
                content, timestamp = self._cache[cache_key]
                if self._is_cache_valid((content, timestamp)):
                    return content
                    
        # Apply rate limiting
        host = urlparse(url).netloc
        await self._rate_limit_request(host)
        
        # Make request
        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                content = await response.text()
                
                # Cache the response
                if self.enable_cache:
                    cache_key = self._get_cache_key(url)
                    self._cache[cache_key] = (content, time.time())
                    
                return content
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to fetch {url}: {e}")
            
    async def fetch_multiple(self, urls: List[str], max_concurrent: int = 10) -> List[Tuple[str, Optional[str]]]:
        """
        Fetch multiple URLs concurrently with controlled concurrency.
        
        Args:
            urls: List of URLs to fetch
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of tuples (url, html_content_or_error)
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(url: str) -> Tuple[str, Optional[str]]:
            async with semaphore:
                try:
                    html = await self.fetch_html(url)
                    return url, html
                except Exception as e:
                    return url, None
                    
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append((str(result), None))
            else:
                processed_results.append(result)
                
        return processed_results
        
    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._cache.clear()
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)
        valid_entries = sum(1 for entry in self._cache.values() if self._is_cache_valid(entry))
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'invalid_entries': total_entries - valid_entries,
            'cache_size_mb': sum(len(content.encode()) for content, _ in self._cache.values()) / (1024 * 1024)
        }


class AsyncHTMLParser:
    """Async wrapper for HTML parsing with selectolax."""
    
    @staticmethod
    def parse_html(html: str) -> HTMLParser:
        """Parse HTML content."""
        return HTMLParser(html)
        
    @staticmethod
    async def parse_html_async(html: str) -> HTMLParser:
        """Parse HTML content in async context."""
        # Run parsing in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, HTMLParser, html)


class AsyncScrapingSession:
    """High-level async scraping session with HTTP client and parsing."""
    
    def __init__(self, **client_kwargs):
        """Initialize scraping session."""
        self.client = AsyncHTTPClient(**client_kwargs)
        self.parser = AsyncHTMLParser()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.client.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
        
    async def fetch_and_parse(self, url: str) -> HTMLParser:
        """Fetch URL and return parsed HTML."""
        html = await self.client.fetch_html(url)
        return await self.parser.parse_html_async(html)
        
    async def fetch_multiple_and_parse(self, urls: List[str], max_concurrent: int = 10) -> List[Tuple[str, Optional[HTMLParser]]]:
        """Fetch multiple URLs and return parsed HTML."""
        results = await self.client.fetch_multiple(urls, max_concurrent)
        
        parsed_results = []
        for url, html in results:
            if html:
                try:
                    parser = await self.parser.parse_html_async(html)
                    parsed_results.append((url, parser))
                except Exception:
                    parsed_results.append((url, None))
            else:
                parsed_results.append((url, None))
                
        return parsed_results
