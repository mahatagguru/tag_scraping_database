#!/usr/bin/env python3
"""
Core functionality tests for the TAG Grading Scraper.
Tests the essential components after cleanup.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_models_import():
    """Test that models module can be imported."""
    try:
        import models
        assert models is not None
    except ImportError as e:
        pytest.fail(f"Failed to import models: {e}")


def test_database_import():
    """Test that database module can be imported."""
    try:
        from db import SessionLocal
        assert SessionLocal is not None
    except ImportError as e:
        pytest.fail(f"Failed to import database module: {e}")


def test_async_pipeline_import():
    """Test that async pipeline can be imported."""
    try:
        from scraper.async_pipeline import AsyncScrapingPipeline, AsyncPipelineConfig
        assert AsyncScrapingPipeline is not None
        assert AsyncPipelineConfig is not None
    except ImportError as e:
        pytest.fail(f"Failed to import async pipeline: {e}")


def test_async_client_import():
    """Test that async client can be imported."""
    try:
        from scraper.async_client import AsyncHTTPClient, AsyncScrapingSession
        assert AsyncHTTPClient is not None
        assert AsyncScrapingSession is not None
    except ImportError as e:
        pytest.fail(f"Failed to import async client: {e}")


def test_async_db_import():
    """Test that async database module can be imported."""
    try:
        from scraper.async_db import AsyncDatabasePool, get_async_session
        assert AsyncDatabasePool is not None
        assert get_async_session is not None
    except ImportError as e:
        pytest.fail(f"Failed to import async database module: {e}")


def test_async_scraper_import():
    """Test that async scraper can be imported."""
    try:
        from scraper.async_scraper import AsyncWebScraper
        assert AsyncWebScraper is not None
    except ImportError as e:
        pytest.fail(f"Failed to import async scraper: {e}")


def test_cache_manager_import():
    """Test that cache manager can be imported."""
    try:
        from scraper.cache_manager import CacheManager, ScrapingCacheManager
        assert CacheManager is not None
        assert ScrapingCacheManager is not None
    except ImportError as e:
        pytest.fail(f"Failed to import cache manager: {e}")


def test_monitoring_import():
    """Test that monitoring module can be imported."""
    try:
        from scraper.monitoring import PerformanceMetrics, Profiler, get_monitoring_manager
        assert PerformanceMetrics is not None
        assert Profiler is not None
        assert get_monitoring_manager is not None
    except ImportError as e:
        pytest.fail(f"Failed to import monitoring module: {e}")


def test_bulk_operations_import():
    """Test that bulk operations can be imported."""
    try:
        from scraper.bulk_db_operations import BulkDatabaseOperations
        assert BulkDatabaseOperations is not None
    except ImportError as e:
        pytest.fail(f"Failed to import bulk operations: {e}")


def test_db_helpers_import():
    """Test that database helpers can be imported."""
    try:
        from scraper.db_helpers import upsert_category, upsert_year, upsert_set
        assert upsert_category is not None
        assert upsert_year is not None
        assert upsert_set is not None
    except ImportError as e:
        pytest.fail(f"Failed to import database helpers: {e}")


def test_audit_import():
    """Test that audit module can be imported."""
    try:
        from scraper.audit import AuditLogger
        assert AuditLogger is not None
    except ImportError as e:
        pytest.fail(f"Failed to import audit module: {e}")


def test_async_pipeline_config():
    """Test that async pipeline configuration works."""
    from scraper.async_pipeline import AsyncPipelineConfig
    
    config = AsyncPipelineConfig(
        max_concurrent_requests=10,
        rate_limit=1.0,
        batch_size=100,
        enable_caching=True,
        enable_monitoring=True
    )
    
    assert config.max_concurrent_requests == 10
    assert config.rate_limit == 1.0
    assert config.batch_size == 100
    assert config.enable_caching is True
    assert config.enable_monitoring is True


if __name__ == "__main__":
    # Run all tests
    test_models_import()
    test_database_import()
    test_async_pipeline_import()
    test_async_client_import()
    test_async_db_import()
    test_async_scraper_import()
    test_cache_manager_import()
    test_monitoring_import()
    test_bulk_operations_import()
    test_db_helpers_import()
    test_audit_import()
    test_async_pipeline_config()
    
    print("✅ All core functionality tests passed!")
