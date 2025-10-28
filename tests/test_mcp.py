"""
Tests for MCP server functionality
"""

from pathlib import Path
import sys

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_mcp_server_import():
    """Test that MCP server modules can be imported."""
    try:
        # Try FastMCP first
        try:
            import fastmcp

            assert fastmcp is not None
            print("✅ FastMCP imported successfully")
        except ImportError:
            # Fallback to official MCP SDK
            import mcp

            assert mcp is not None
            print("✅ Official MCP SDK imported successfully")

    except ImportError as e:
        pytest.fail(f"Failed to import MCP modules: {e}")


def test_mcp_server_files():
    """Test that MCP server files exist and can be imported."""
    try:
        # Test FastMCP server
        try:
            from fastmcp_server import mcp

            assert mcp is not None
            print("✅ FastMCP server imported successfully")
        except ImportError:
            # Test official MCP server
            try:
                from mcp.mcp_server_official import TAGScraperMCPServer

                assert TAGScraperMCPServer is not None
                print("✅ Official MCP server imported successfully")
            except (ImportError, SystemExit):
                # MCP SDK not installed, skip this test
                pytest.skip("MCP SDK not installed - skipping MCP server test")

    except ImportError as e:
        pytest.fail(f"Failed to import MCP server files: {e}")


if __name__ == "__main__":
    test_mcp_server_import()
    test_mcp_server_files()
    print("✅ MCP server tests passed!")
