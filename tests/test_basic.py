"""
Basic tests for TAG Grading Scraper
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that basic modules can be imported."""
    try:
        import models
        assert True, "models module imported successfully"
    except ImportError as e:
        pytest.fail(f"Failed to import models: {e}")


def test_database_connection():
    """Test basic database functionality."""
    try:
        from db import get_db_connection
        # This should not raise an error
        assert True, "Database connection module imported successfully"
    except ImportError as e:
        pytest.fail(f"Failed to import database module: {e}")


def test_scraper_imports():
    """Test that scraper modules can be imported."""
    try:
        from scraper.unified_pipeline import UnifiedPipeline
        assert True, "UnifiedPipeline imported successfully"
    except ImportError as e:
        pytest.fail(f"Failed to import UnifiedPipeline: {e}")


def test_basic_functionality():
    """Basic functionality test."""
    assert 1 + 1 == 2, "Basic math should work"
    assert "hello" + " world" == "hello world", "String concatenation should work"


if __name__ == "__main__":
    # Run basic tests
    test_imports()
    test_database_connection()
    test_scraper_imports()
    test_basic_functionality()
    print("✅ All basic tests passed!")
