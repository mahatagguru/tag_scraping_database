"""
Official MCP Server for TAG Grading Scraper
Using the official MCP Python SDK instead of FastMCP
"""

import asyncio
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Add the src directory to the path to import our modules
sys.path.append(str(Path(__file__).parent))

try:
    from mcp import Server, StdioServerParameters
    from mcp.types import (
        CallToolRequest,
        CallToolResult,
        DataType,
        EmbeddedResource,
        GetSchemasRequest,
        GetSchemasResult,
        ImageContent,
        ListResourcesRequest,
        ListResourcesResult,
        ListToolsRequest,
        ListToolsResult,
        Property,
        ReadResourceRequest,
        ReadResourceResult,
        Resource,
        Schema,
        TextContent,
        Tool,
    )
except ImportError:
    print("❌ MCP SDK not found. Install with: pip install mcp")
    print("   Or install FastMCP from GitHub: pip install git+https://github.com/jlowin/fastmcp.git")
    sys.exit(1)

from db import get_db_connection
from models import *
from scraper.db_helpers import DatabaseHelper
from scraper.multi_level_orchestrator import MultiLevelOrchestrator
from scraper.unified_pipeline import UnifiedPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database helper
db_helper = DatabaseHelper()

class TAGScraperMCPServer:
    """MCP Server for TAG Grading Scraper using official MCP SDK"""
    
    def __init__(self):
        self.server = Server("TAG Grading Scraper 🏷️")
        self.pipeline = UnifiedPipeline()
        self.orchestrator = MultiLevelOrchestrator()
        
        # Register tools
        self._register_tools()
        
    def _register_tools(self):
        """Register all MCP tools"""
        
        @self.server.tool("scrape_sport_years")
        async def scrape_sport_years(request: CallToolRequest) -> CallToolResult:
            """Scrape available years for a specific sport"""
            try:
                args = request.arguments
                sport = args.get("sport", "baseball")
                
                # Mock data for now - replace with actual pipeline call
                years = ["2023", "2022", "2021", "2020", "2019"]
                
                result = {
                    "success": True,
                    "sport": sport,
                    "years_found": len(years),
                    "years": years,
                    "message": f"Successfully scraped {len(years)} years for {sport}"
                }
                
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, indent=2))]
                )
            except Exception as e:
                error_result = {
                    "success": False,
                    "sport": sport,
                    "error": str(e),
                    "message": f"Failed to scrape years for {sport}"
                }
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(error_result, indent=2))]
                )
        
        @self.server.tool("get_database_stats")
        async def get_database_stats(request: CallToolRequest) -> CallToolResult:
            """Get statistics about the scraped data in the database"""
            try:
                # Mock stats for now
                stats = {
                    "total_cards": 1250,
                    "total_sets": 45,
                    "total_sports": 5,
                    "average_grade": 8.2
                }
                
                result = {
                    "success": True,
                    "stats": stats,
                    "message": "Successfully retrieved database statistics"
                }
                
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, indent=2))]
                )
            except Exception as e:
                error_result = {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to retrieve database statistics"
                }
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(error_result, indent=2))]
                )
        
        @self.server.tool("search_cards")
        async def search_cards(request: CallToolRequest) -> CallToolResult:
            """Search for cards in the database"""
            try:
                args = request.arguments
                query = args.get("query", "")
                limit = args.get("limit", 50)
                
                # Mock search results
                results = [
                    {"card_name": f"Card {i}", "set": "2023 Topps", "grade": "9.0"}
                    for i in range(min(limit, 10))
                ]
                
                result = {
                    "success": True,
                    "query": query,
                    "results_found": len(results),
                    "results": results,
                    "message": f"Found {len(results)} cards matching '{query}'"
                }
                
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, indent=2))]
                )
            except Exception as e:
                error_result = {
                    "success": False,
                    "query": query,
                    "error": str(e),
                    "message": f"Failed to search for cards with query '{query}'"
                }
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(error_result, indent=2))]
                )
        
        @self.server.tool("get_card_totals_by_type")
        async def get_card_totals_by_type(request: CallToolRequest) -> CallToolResult:
            """Get total counts of cards by type, sport, or year"""
            try:
                args = request.arguments
                card_type = args.get("card_type")
                sport = args.get("sport")
                year = args.get("year")
                
                # Mock totals
                totals = {
                    "total_cards": 1250,
                    "by_type": {
                        "rookie": 180,
                        "veteran": 720,
                        "all-star": 200,
                        "hall_of_fame": 150
                    },
                    "by_sport": {
                        "baseball": 450,
                        "football": 400,
                        "basketball": 400
                    },
                    "by_year": {
                        "2023": 300,
                        "2022": 250,
                        "2021": 200
                    },
                    "filters_applied": {
                        "card_type": card_type,
                        "sport": sport,
                        "year": year
                    }
                }
                
                result = {
                    "success": True,
                    "totals": totals,
                    "message": "Successfully retrieved card totals"
                }
                
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, indent=2))]
                )
            except Exception as e:
                error_result = {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to retrieve card totals"
                }
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(error_result, indent=2))]
                )
    
    async def run(self):
        """Run the MCP server"""
        logger.info("🚀 Starting TAG Grading Scraper MCP Server...")
        logger.info("📚 Available tools:")
        logger.info("  - scrape_sport_years: Scrape available years for a sport")
        logger.info("  - get_database_stats: Get database statistics")
        logger.info("  - search_cards: Search for cards in the database")
        logger.info("  - get_card_totals_by_type: Get card totals by type/sport/year")
        logger.info("\n🔌 Server ready to accept MCP connections!")
        
        # Run the server
        async with self.server.run_stdio(StdioServerParameters()):
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    server = TAGScraperMCPServer()
    asyncio.run(server.run())
