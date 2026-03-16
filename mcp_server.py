#!/usr/bin/env python3
"""
Entry point for the TAG Grading MCP server.

Usage:
    python mcp_server.py

Or register in claude_desktop_config.json:
    {
      "mcpServers": {
        "tag-grading": {
          "command": "python",
          "args": ["/absolute/path/to/tag_scraping_database/mcp_server.py"]
        }
      }
    }

All diagnostic output (DB connection status, errors) goes to stderr.
stdout is reserved exclusively for the MCP stdio transport protocol.
"""

import asyncio
import os
import sys

# Ensure the project root is on the Python path so that
# "src.*" imports resolve correctly.
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from src.mcp_server import main  # noqa: E402

if __name__ == "__main__":
    asyncio.run(main())
