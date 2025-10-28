"""
Tests for database models
"""

from pathlib import Path
import sys

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_models_import():
    """Test that models can be imported."""
    try:
        import models

        assert models is not None
    except ImportError as e:
        pytest.fail(f"Failed to import models: {e}")


def test_models_structure():
    """Test that models have expected structure."""
    try:
        import models

        # Check if key classes exist
        assert hasattr(models, "Base"), "Base class should exist"

        # Add more specific model checks as needed
        assert True, "Models structure is valid"

    except Exception as e:
        pytest.fail(f"Models structure test failed: {e}")


if __name__ == "__main__":
    test_models_import()
    test_models_structure()
    print("✅ Models tests passed!")
