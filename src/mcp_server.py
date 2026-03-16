#!/usr/bin/env python3
"""
MCP (Model Context Protocol) server for TAG Grading population data.

Exposes 10 tools that allow Claude and other MCP clients to query the
TAG Grading population database by sport, year, set, card, and cert number.

Run via:
    python mcp_server.py          (from project root)
    python -m src.mcp_server      (from project root)

Or register in claude_desktop_config.json:
    {
      "mcpServers": {
        "tag-grading": {
          "command": "python",
          "args": ["/path/to/tag_scraping_database/mcp_server.py"]
        }
      }
    }
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import mcp.server.stdio
from mcp.server import Server
from mcp.types import TextContent, Tool

# Import the query engine (all DB output goes to stderr automatically)
from src.mcp_query_engine import (
    get_card_population,
    get_database_stats,
    get_set_population_summary,
    get_sport_overview,
    get_top_graded_cards,
    list_sets,
    list_sports,
    list_years,
    lookup_cert,
    search_cards,
)

# ---------------------------------------------------------------------------
# Server definition
# ---------------------------------------------------------------------------

app = Server("tag-grading-population")

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

_TOOLS: list[Tool] = [
    Tool(
        name="list_sports",
        description=(
            "List all sports/categories available in the TAG Grading database, "
            "with the number of years and sets scraped for each sport."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="list_years",
        description=(
            "List all years available for a given sport, along with how many "
            "sets were graded in each year."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "sport": {
                    "type": "string",
                    "description": "Sport name, e.g. 'Baseball', 'Hockey', 'Basketball'",
                }
            },
            "required": ["sport"],
        },
    ),
    Tool(
        name="list_sets",
        description=(
            "List all card sets for a given sport and year, with card counts "
            "and any available metrics."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "sport": {
                    "type": "string",
                    "description": "Sport name, e.g. 'Baseball'",
                },
                "year": {
                    "type": "string",
                    "description": "Year as a string, e.g. '1989'",
                },
            },
            "required": ["sport", "year"],
        },
    ),
    Tool(
        name="search_cards",
        description=(
            "Search for cards by name across the entire database. "
            "Optionally narrow by sport and/or year. "
            "Returns matching cards sorted by how many graded copies exist."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Partial card name to search for, e.g. 'Griffey', 'Jordan'",
                },
                "sport": {
                    "type": "string",
                    "description": "Optional sport filter, e.g. 'Baseball'",
                },
                "year": {
                    "type": "string",
                    "description": "Optional year filter, e.g. '1989'",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return (default 50)",
                    "default": 50,
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="get_card_population",
        description=(
            "Get the complete grade distribution (population count) for a specific card. "
            "Shows how many copies of the card exist at each TAG grade, plus percentages."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "sport": {
                    "type": "string",
                    "description": "Sport name, e.g. 'Baseball'",
                },
                "year": {
                    "type": "string",
                    "description": "Year as a string, e.g. '1989'",
                },
                "set_title": {
                    "type": "string",
                    "description": "Set name, e.g. 'Upper Deck'",
                },
                "card_name": {
                    "type": "string",
                    "description": "Card name exactly as stored, e.g. 'Ken Griffey Jr.'",
                },
            },
            "required": ["sport", "year", "set_title", "card_name"],
        },
    ),
    Tool(
        name="get_set_population_summary",
        description=(
            "Get the aggregate grade distribution for all cards within a set. "
            "Useful for understanding how a full set grades out across all TAG grades."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "sport": {
                    "type": "string",
                    "description": "Sport name, e.g. 'Baseball'",
                },
                "year": {
                    "type": "string",
                    "description": "Year as a string, e.g. '1989'",
                },
                "set_title": {
                    "type": "string",
                    "description": "Set name, e.g. 'Topps'",
                },
            },
            "required": ["sport", "year", "set_title"],
        },
    ),
    Tool(
        name="get_sport_overview",
        description=(
            "Get a high-level overview of a sport in the TAG database: "
            "how many years, sets, and cards are tracked, total graded, "
            "and the overall grade breakdown."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "sport": {
                    "type": "string",
                    "description": "Sport name, e.g. 'Baseball'",
                }
            },
            "required": ["sport"],
        },
    ),
    Tool(
        name="lookup_cert",
        description=(
            "Look up a specific TAG certificate number to find which card it belongs to, "
            "what grade it received, its rank, and when it was graded."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "cert_number": {
                    "type": "string",
                    "description": "TAG certificate number, e.g. '1234567'",
                }
            },
            "required": ["cert_number"],
        },
    ),
    Tool(
        name="get_top_graded_cards",
        description=(
            "Find cards with the highest population at a specific TAG grade. "
            "Optionally filter by sport and/or year. Useful for finding the most "
            "frequently submitted cards at a given grade."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "grade": {
                    "type": "string",
                    "description": "TAG grade to query, e.g. '10', '9.5', '9'",
                },
                "sport": {
                    "type": "string",
                    "description": "Optional sport filter",
                },
                "year": {
                    "type": "string",
                    "description": "Optional year filter",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return (default 20)",
                    "default": 20,
                },
            },
            "required": ["grade"],
        },
    ),
    Tool(
        name="get_database_stats",
        description=(
            "Return overall statistics for the TAG Grading database: "
            "total certificates, sports, years, sets, cards, and when data was last scraped."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
]


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


@app.list_tools()
async def list_tools() -> list[Tool]:
    return _TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Dispatch tool calls to the query engine and return JSON results."""

    def _result(data: Any) -> list[TextContent]:
        return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]

    def _error(msg: str) -> list[TextContent]:
        return [TextContent(type="text", text=json.dumps({"error": msg}, indent=2))]

    try:
        if name == "list_sports":
            return _result(list_sports())

        elif name == "list_years":
            sport = arguments.get("sport", "")
            if not sport:
                return _error("'sport' is required")
            return _result(list_years(sport))

        elif name == "list_sets":
            sport = arguments.get("sport", "")
            year = arguments.get("year", "")
            if not sport or not year:
                return _error("'sport' and 'year' are required")
            return _result(list_sets(sport, year))

        elif name == "search_cards":
            query = arguments.get("query", "")
            if not query:
                return _error("'query' is required")
            return _result(
                search_cards(
                    query=query,
                    sport=arguments.get("sport"),
                    year=arguments.get("year"),
                    limit=int(arguments.get("limit", 50)),
                )
            )

        elif name == "get_card_population":
            required = ["sport", "year", "set_title", "card_name"]
            missing = [f for f in required if not arguments.get(f)]
            if missing:
                return _error(f"Missing required fields: {missing}")
            return _result(
                get_card_population(
                    sport=arguments["sport"],
                    year=arguments["year"],
                    set_title=arguments["set_title"],
                    card_name=arguments["card_name"],
                )
            )

        elif name == "get_set_population_summary":
            required = ["sport", "year", "set_title"]
            missing = [f for f in required if not arguments.get(f)]
            if missing:
                return _error(f"Missing required fields: {missing}")
            return _result(
                get_set_population_summary(
                    sport=arguments["sport"],
                    year=arguments["year"],
                    set_title=arguments["set_title"],
                )
            )

        elif name == "get_sport_overview":
            sport = arguments.get("sport", "")
            if not sport:
                return _error("'sport' is required")
            return _result(get_sport_overview(sport))

        elif name == "lookup_cert":
            cert = arguments.get("cert_number", "")
            if not cert:
                return _error("'cert_number' is required")
            result = lookup_cert(cert)
            if result is None:
                return _result({"found": False, "cert_number": cert})
            result["found"] = True
            return _result(result)

        elif name == "get_top_graded_cards":
            grade = arguments.get("grade", "")
            if not grade:
                return _error("'grade' is required")
            return _result(
                get_top_graded_cards(
                    grade=grade,
                    sport=arguments.get("sport"),
                    year=arguments.get("year"),
                    limit=int(arguments.get("limit", 20)),
                )
            )

        elif name == "get_database_stats":
            return _result(get_database_stats())

        else:
            return _error(f"Unknown tool: {name}")

    except Exception as exc:
        print(f"[mcp_server] Tool '{name}' raised: {exc}", file=sys.stderr)
        return _error(f"Internal error: {exc}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the MCP server over stdio."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
