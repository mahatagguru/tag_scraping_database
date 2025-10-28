"""
Pytest configuration for TAG Grading Scraper tests
"""

import os
from pathlib import Path
import sys

import pytest

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def src_directory():
    """Provide the src directory path."""
    return src_path


@pytest.fixture(scope="session")
def test_data_directory():
    """Provide the test data directory path."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="function")
def clean_environment():
    """Clean up environment variables after each test."""
    original_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(original_env)
