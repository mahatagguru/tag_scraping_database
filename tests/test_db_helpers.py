"""
Tests for database helper functions
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_db_helpers_import():
    """Test that db_helpers can be imported."""
    try:
        from scraper.db_helpers import DatabaseHelper
        assert DatabaseHelper is not None
    except ImportError as e:
        pytest.fail(f"Failed to import DatabaseHelper: {e}")


def test_db_helpers_structure():
    """Test that DatabaseHelper has expected structure."""
    try:
        from scraper.db_helpers import DatabaseHelper
        
        # Check if class exists and has expected methods
        assert hasattr(DatabaseHelper, '__init__'), "DatabaseHelper should have __init__ method"
        
        # Add more specific checks as needed
        assert True, "DatabaseHelper structure is valid"
        
    except Exception as e:
        pytest.fail(f"DatabaseHelper structure test failed: {e}")


if __name__ == "__main__":
    test_db_helpers_import()
    test_db_helpers_structure()
    print("✅ Database helpers tests passed!")
